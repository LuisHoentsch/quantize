import cv2
import numpy as np

def apply_bilateral_filter(image: np.ndarray, d: int = 9, sigma_color: float = 75.0, sigma_space: float = 75.0, passes: int = 1) -> np.ndarray:
    filtered = image
    for _ in range(passes):
        filtered = cv2.bilateralFilter(filtered, d, sigma_color, sigma_space)
    return filtered

def apply_median_blur(image: np.ndarray, ksize: int = 5, passes: int = 1) -> np.ndarray:
    filtered = image
    for _ in range(passes):
        filtered = cv2.medianBlur(filtered, ksize)
    return filtered

def quantize_brightness(image: np.ndarray, num_colors: int) -> np.ndarray:
    if num_colors > 1:
        bin_size = 256 // num_colors
        quantization_factor = 255 // (num_colors - 1)
        quantized = (image // bin_size) * quantization_factor
        return np.clip(quantized, 0, 255).astype(np.uint8)
    return image

def quantize_colors_kmeans(image: np.ndarray, num_colors: int) -> np.ndarray:
    if num_colors <= 1:
        return image

    # Reshape the image array to a 2D array of pixels
    Z = image.reshape((-1, 3))

    # Convert to np.float32 for kmeans
    Z = np.float32(Z)

    # Define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, label, center = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Convert back into uint8 and reshape to original image dimensions
    center = np.uint8(center)
    res = center[label.flatten()]
    return res.reshape((image.shape))

def downscale_image(image: np.ndarray, max_dim: int) -> tuple[np.ndarray, tuple[int, int]]:
    original_size = (image.shape[1], image.shape[0]) # (width, height)
    max_current_dim = max(original_size)

    if max_current_dim <= max_dim:
        return image, original_size

    scale_factor = max_dim / max_current_dim
    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA), original_size

def upscale_image(image: np.ndarray, original_size: tuple[int, int]) -> np.ndarray:
    current_size = (image.shape[1], image.shape[0])
    if current_size == original_size:
        return image
    # We use INTER_NEAREST to preserve the quantized colors
    return cv2.resize(image, original_size, interpolation=cv2.INTER_NEAREST)

def apply_stylization(
    image: np.ndarray,

    num_colors: int = 3,
    num_shades_per_color: int = 3,

    d: int = 15,
    sigma_color: float = 75.0,
    sigma_space: float = 75.0,
    passes: int = 5,

    ksize: int = 7,

    max_dim: int = 1000,
#    debug_dir: str = None,
) -> np.ndarray:
    """
    Core image processing logic.
    Applies filtering and brightness quantization to an image array.
    Works purely on NumPy arrays to make it testable and easy to integrate into an API.
    """
    #if debug_dir:
    #    os.makedirs(debug_dir, exist_ok=True)

    #def save_debug(img_to_save, filename):
    #    if debug_dir:
    #        cv2.imwrite(os.path.join(debug_dir, filename), img_to_save)

    scaled_image, original_size = downscale_image(image, max_dim)
    #save_debug(scaled_image, "1_downscaled.jpg")

    # Step 1 & 2 logic combined:
    # Apply established filters
    filtered_color = apply_median_blur(scaled_image, ksize, passes)
    #save_debug(filtered_color, "2_median_blur.jpg")

    filtered_color = apply_bilateral_filter(filtered_color, d, sigma_color, sigma_space, passes)
    #save_debug(filtered_color, "3_bilateral.jpg")

    # Step 1: Segment the picture into base colors
    Z = filtered_color.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, base_labels, base_centers = cv2.kmeans(Z, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    base_labels = base_labels.flatten()

    # Save base colors debug
    base_img = np.uint8(base_centers)[base_labels].reshape(scaled_image.shape)
    #save_debug(base_img, "4_base_colors.jpg")

    # Step 2: For each base color mask, extract 'num_colors' shades
    result_flat = np.zeros_like(Z)

    for i in range(num_colors):
        mask = (base_labels == i)
        if not np.any(mask):
            continue

        mask_pixels = Z[mask]
        if len(mask_pixels) >= num_shades_per_color and num_shades_per_color > 1:
            # K-Means to find 'num_colors' shades for this specific base color sector
            _, shade_labels, shade_centers = cv2.kmeans(mask_pixels, num_shades_per_color, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            shade_centers = np.uint8(shade_centers)
            result_flat[mask] = shade_centers[shade_labels.flatten()]
        else:
            result_flat[mask] = np.uint8(mask_pixels)

        # Optional debug for individual steps
        #if debug_dir:
        #    step_img = np.zeros_like(Z)
        #    step_img[mask] = result_flat[mask]
            #save_debug(step_img.reshape(scaled_image.shape).astype(np.uint8), f"4_base_color_mask_{i}_shades.jpg")

    quantized = result_flat.reshape(scaled_image.shape).astype(np.uint8)
    #save_debug(quantized, "5_two_step_shades.jpg")

    upscaled = upscale_image(quantized, original_size)
    #save_debug(upscaled, "6_upscaled.jpg")

    return upscaled


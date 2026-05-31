import argparse
import cv2
from stylizer import apply_stylization

def process_image(
    input_path: str,
    output_path: str,
    num_colors: int = 3,
    num_shades: int = 5,
    d: int = 15,
    sigma_color: float = 75.0,
    sigma_space: float = 75.0,
    passes: int = 5,
    ksize: int = 5,
    max_dim: int = 1000
) -> None:
    """
    Loads an image from disk, applies stylization, and saves the output.
    """
    # Task 1.1: Image Loading & Setup
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Could not load image at {input_path}")

    # Apply processing
    result = apply_stylization(
        img,
        num_colors=num_colors,
        num_shades_per_color=num_shades,
        d=d,
        sigma_color=sigma_color,
        sigma_space=sigma_space,
        passes=passes,
        ksize=ksize,
        max_dim=max_dim
    )

    # Task 1.5: Image Output
    success = cv2.imwrite(output_path, result)
    if not success:
        raise IOError(f"Failed to save image to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Image Stylization Pipeline")
    parser.add_argument("input_path", type=str, help="Path to input image")
    parser.add_argument("output_path", type=str, help="Path to output image")
    parser.add_argument("--num_colors", type=int, default=3, help="Number of base colors to segment the image into")
    parser.add_argument("--num_shades", type=int, default=5, help="Number of shades per base color")
    parser.add_argument("--d", type=int, default=15, help="Bilateral: Diameter of each pixel neighborhood")
    parser.add_argument("--sigma_color", type=float, default=75.0, help="Bilateral: Filter sigma in the color space")
    parser.add_argument("--sigma_space", type=float, default=75.0, help="Bilateral: Filter sigma in the coordinate space")
    parser.add_argument("--passes", type=int, default=5, help="Number of filter passes")
    parser.add_argument("--ksize", type=int, default=5, help="Median: Kernel size (must be odd)")
    parser.add_argument("--max_dim", type=int, default=1000, help="Maximum dimension (width or height) to downscale image before processing")

    args = parser.parse_args()

    process_image(
        args.input_path, args.output_path, args.num_colors, args.num_shades,
        args.d, args.sigma_color, args.sigma_space, args.passes,
        args.ksize, args.max_dim
    )
    print(f"Processed image successfully saved to {args.output_path}")

if __name__ == "__main__":
    main()

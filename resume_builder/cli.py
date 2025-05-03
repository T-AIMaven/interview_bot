import argparse
import time

from autocv_core import AutoCV  # Assume these handle logic internally

def main():
    parser = argparse.ArgumentParser(prog="autocv", description="Auto Resume Generator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # upload_resume command
    upload_parser = subparsers.add_parser("upload_resume", help="Upload a resume file")
    upload_parser.add_argument("resume_path", type=str, help="Path to resume file (.pdf or .docx)")

    # generate command
    generate_parser = subparsers.add_parser("generate", help="Generate resume, cover letter, or both")
    generate_parser.add_argument('-j', "--jd", required=True, help="Path to job description file")
    generate_parser.add_argument('-t', "--target", choices=["resume", "cover_letter", "both"], default="both", help="What to generate")
    generate_parser.add_argument('-o', "--output_dir", default=".", help="Directory to save results")
    generate_parser.add_argument('-f', "--format", choices=["docx", "pdf", "both"], default="both", help="Output file format")

    # easy generate command
    easy_generate_parser = subparsers.add_parser("easy_generate", help="Generate resume, cover letter, or both easily")
    easy_generate_parser.add_argument('-r', "--resume", required=True, help="Path to resume file")
    easy_generate_parser.add_argument('-j', "--jd", required=True, help="Path to job description file")
    easy_generate_parser.add_argument('-t', "--target", choices=["resume", "cover_letter", "both"], default="both", help="What to generate")
    easy_generate_parser.add_argument('-o', "--output_dir", default=".", help="Directory to save results")
    easy_generate_parser.add_argument('-f', "--format", choices=["docx", "pdf", "both"], default="both", help="Output file format")

    args = parser.parse_args()

    autocv = AutoCV()
    # time calculation
    start_time = time.time()

    if args.command == "upload_resume":
        autocv.upload_resume(args.resume_path)

    elif args.command == "generate":
        result = autocv.generate_output(
            jd_path=args.jd,
            target=args.target,
            output_dir=args.output_dir,
            output_format=args.format
        )

        print(f"Generated files saved.\n{result}:")

    elif args.command == "easy_generate":
        result = autocv.generate_output(
            resume_path=args.resume,
            jd_path=args.jd,
            target=args.target,
            output_dir=args.output_dir,
            output_format=args.format,
            method="easy"
        )

        print(f"Generated files saved.\n{result}:")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Execution time: {elapsed_time:.2f} seconds")
    print("Done!")

if __name__ == "__main__":
    main()

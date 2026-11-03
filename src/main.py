from pathlib import Path

file_path = Path("test/time_tracking.md")

def main():
    content = file_path.read_bytes()
    print(f"Bytes: {len(content)}")

if __name__ == "__main__":
    main()

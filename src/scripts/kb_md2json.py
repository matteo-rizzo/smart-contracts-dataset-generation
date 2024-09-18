from src.classes.generation.ReentrancyScenarioExtractor import ReentrancyScenarioExtractor

if __name__ == "__main__":
    # Paths for input and output
    input_markdown_file = 'kb.md'
    output_directory = 'kb'

    extractor = ReentrancyScenarioExtractor(input_file=input_markdown_file, output_dir=output_directory)
    extractor.extract_and_save()

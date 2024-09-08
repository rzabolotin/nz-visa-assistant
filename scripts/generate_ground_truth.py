import json
import random
import argparse
import os
from anthropic import Anthropic

clientA = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def llm(prompt):
    response = clientA.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return response.content[0].text


def generate_questions(content, n_questions):
    prompt = f"""Based on the following content, generate {n_questions} diverse questions that can be answered using this information. Provide only the questions, one per line without numbering:

Content:
{content}

Questions:"""

    questions = [q.strip() for q in llm(prompt).strip().split('\n') if q.strip()]
    return questions[:n_questions]  # Ensure we only return the requested number of questions


def create_ground_truth(data, n_questions_per_fact, n_iter):
    ground_truth = []
    urls = list(data.keys())

    for i in range(n_iter):
        url = random.choice(urls)
        content = data[url]['main_content']

        if not content:
            print(f"Iteration {i + 1}/{n_iter}: Skipping empty content for URL: {url}")
            continue

        print(f"Iteration {i + 1}/{n_iter}: Generating questions for URL: {url}")
        questions = generate_questions(content, n_questions_per_fact)

        for question in questions:
            ground_truth.append({
                "question": question,
                "url": url
            })

        print(f"  Generated {len(questions)} questions")

    return ground_truth


def save_ground_truth(ground_truth, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate ground truth dataset for retrieval system evaluation")
    parser.add_argument("--input", default="data/site_content.json", help="Input JSON file path")
    parser.add_argument("--output", default="data/ground-truth.json", help="Output JSON file path")
    parser.add_argument("--n_questions_per_fact", type=int, default=5, help="Number of questions per fact")
    parser.add_argument("--n_iter", type=int, default=100, help="Number of iterations")
    args = parser.parse_args()

    data = load_json_data(args.input)
    print(f"Loaded data from {args.input}")
    print(
        f"Starting ground truth generation with {args.n_iter} iterations and {args.n_questions_per_fact} questions per fact")

    ground_truth = create_ground_truth(data, args.n_questions_per_fact, args.n_iter)
    save_ground_truth(ground_truth, args.output)

    print(f"Ground truth dataset with {len(ground_truth)} questions has been generated and saved to {args.output}")


if __name__ == "__main__":
    main()
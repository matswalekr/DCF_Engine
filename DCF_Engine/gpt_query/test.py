from gpt_query import LLM_Query_Handler


def main()-> None:
    query = LLM_Query_Handler()

    answer: str = query.prompt("Who was the 2nd president of the United States of America?")
    print(answer)

if __name__ == "__main__":
    main()
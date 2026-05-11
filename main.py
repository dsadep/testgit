from dotenv import load_dotenv
from commands.parser import Parser

load_dotenv()

if __name__ == '__main__':
    parser = Parser.parser
    args = parser.parse_args()
    args.func(args)
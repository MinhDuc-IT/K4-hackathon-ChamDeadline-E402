import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from src.rag import get_answer
print(get_answer('Tối nay có hoạt động gì không'))

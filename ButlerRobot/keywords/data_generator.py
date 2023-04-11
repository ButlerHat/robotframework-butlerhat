import random
from .utils.vocabulary import get_vocabulary


def get_random_words(n=10):
    vocab = get_vocabulary()
    return random.sample(vocab, n)
    
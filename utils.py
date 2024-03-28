import string
import random

# Generate a short URL method
def generate_short_url(length=6):
  chars = string.ascii_lowercase + string.digits
  return ''.join(random.choice(chars) for _ in range(length))
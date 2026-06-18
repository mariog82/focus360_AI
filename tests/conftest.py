
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['DATABASE_URL']='sqlite:///:memory:'
os.environ['SECRET_KEY']='test'
os.environ['INTERNAL_API_KEY']='test-key'

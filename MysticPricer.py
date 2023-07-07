import ast
import glob
import json
import os
from re import split
import sqlite3
import cv2
import easyocr
import psycopg2
import yaml
from fuzzywuzzy import fuzz
import concurrent.futures

from Card import Card

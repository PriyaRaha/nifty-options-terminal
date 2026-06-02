#!/bin/bash
cd "$(dirname "$0")"
pip install -r requirements.txt -q
streamlit run Home.py

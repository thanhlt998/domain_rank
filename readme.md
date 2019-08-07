# SETTINGS
```
In settings.py
    - DB: host, user, password, db - connect to MySQL server
    - NO_MAX_CONCURRENT_SPIDER: number of concurrent domains to crawl ranking factors
    - SETTINGS:
        ...
        CRITERIA_LIST, CRITERIA_TYPE, CRITERIA_INDEX, COMPARISON_MATRIX: list of criterias, correspondent type (cost/benefit), correspondent indices and comparision matrix between criterias
        
```

# Running
Run crawling ranking factors and ranking domains
### Using python 3, install requirements
```
pip install -r requirements.txt
```
### Including
```
- crawling ranking factors
- calculate pagerank
- calculate ranking score
```
### Command
```
python main.py
```
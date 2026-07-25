# leeter_core/fetch.py
"""Core fetch functionality extracted from cli/fetch.py.

Provides functions to retrieve LeetCode problem metadata and scaffold the problem
folder. The CLI wrapper will import and invoke these functions.
"""

import os
import json
import time
import urllib.request
import urllib.error

def get_session_cookie():
    session_file = os.path.expanduser("~/.lc/session.json")
    if not os.path.exists(session_file):
        return None
    with open(session_file, "r") as f:
        data = json.load(f)
        return data.get("cookie")

def fetch_with_retry(req, max_retries=3):
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Too many requests (429) after retries.")
            elif e.code == 403:
                raise Exception(f"Forbidden (403). Is your session cookie valid/expired? ({e.read().decode('utf-8')})")
            else:
                raise Exception(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        except Exception as e:
            raise e
    return None

def get_title_slug_by_id(frontend_id):
    url = "https://leetcode.com/api/problems/algorithms/"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    data = fetch_with_retry(req)
    if not data or "stat_status_pairs" not in data:
        raise Exception("Failed to fetch algorithms list from LeetCode.")
    for item in data["stat_status_pairs"]:
        stat = item.get("stat", {})
        if str(stat.get("frontend_question_id")) == str(frontend_id):
            return stat.get("question__title_slug")
    raise Exception(f"Question ID {frontend_id} not found in algorithms list.")

def fetch_question_data(title_slug):
    url = "https://leetcode.com/graphql"
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        isPaidOnly
        difficulty
        likes
        dislikes
        isLiked
        isFavor
        status
        sampleTestCase
        exampleTestcases
        metaData
        content
        hints
        companyTagStats
        stats
        similarQuestions
        topicTags {
          name
          slug
          translatedName
        }
        codeSnippets {
          lang
          langSlug
          code
        }
      }
    }
    """
    variables = {"titleSlug": title_slug}
    payload = {"operationName": "questionData", "variables": variables, "query": query}
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Referer", f"https://leetcode.com/problems/{title_slug}/")
    cookie = get_session_cookie()
    if cookie:
        req.add_header("Cookie", cookie)
    response_data = fetch_with_retry(req)
    # Check for premium errors and retry without companyTagStats if needed
    if response_data and "errors" in response_data:
        errors = response_data["errors"]
        if any(e.get("message") == "You are not authorized" or "403" in str(e) for e in errors):
            query_no_premium = query.replace("companyTagStats", "")
            payload["query"] = query_no_premium
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "Mozilla/5.0")
            req.add_header("Referer", f"https://leetcode.com/problems/{title_slug}/")
            if cookie:
                req.add_header("Cookie", cookie)
            response_data = fetch_with_retry(req)
    if response_data and "data" in response_data and response_data["data"]["question"]:
        return response_data["data"]["question"]
    else:
        raise Exception("Question data not found in GraphQL response.")



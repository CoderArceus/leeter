import os
import json
import time
import urllib.request
import urllib.error

def get_session_cookie():
    session_file = os.path.expanduser("~/.lc/session.json")
    if not os.path.exists(session_file):
        return None
    with open(session_file, 'r') as f:
        data = json.load(f)
        return data.get('cookie')

def fetch_with_retry(req, max_retries=3):
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Too many requests (429) after retries.")
            elif e.code == 403:
                # Let the caller handle 403 gracefully if it's on a specific query
                # But for the general GraphQL query, 403 might mean bad cookie or premium only
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
    if not data or 'stat_status_pairs' not in data:
        raise Exception("Failed to fetch algorithms list from LeetCode.")
        
    for item in data['stat_status_pairs']:
        stat = item.get('stat', {})
        if str(stat.get('frontend_question_id')) == str(frontend_id):
            return stat.get('question__title_slug')
            
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
    payload = {
        "operationName": "questionData",
        "variables": variables,
        "query": query
    }
    
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Referer", f"https://leetcode.com/problems/{title_slug}/")
    
    cookie = get_session_cookie()
    if cookie:
        req.add_header("Cookie", cookie)
        
    try:
        response_data = fetch_with_retry(req)
        
        # Check if companyTagStats failed inside GraphQL due to premium
        if response_data and "errors" in response_data:
            # Re-fetch without companyTagStats if it was forbidden
            errors = response_data["errors"]
            if any(e.get("message") == "You are not authorized" or "403" in str(e) for e in errors):
                query_no_premium = query.replace("companyTagStats", "")
                payload["query"] = query_no_premium
                data_bytes = json.dumps(payload).encode('utf-8')
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
    except Exception as e:
        raise Exception(f"Failed to fetch question data: {e}")

def cmd_fetch(args):
    from cli.output import renderer
    from cli.scaffold import scaffold_problem
    from cli.analyzer import run_pipeline_unified
    frontend_id = args.id
    renderer.print(f"Resolving title slug for ID {frontend_id}...")
    try:
        title_slug = get_title_slug_by_id(frontend_id)
        renderer.print(f"Fetching data for {title_slug}...")
        data = fetch_question_data(title_slug)
        folder = scaffold_problem(data, force=getattr(args, 'force', False))
        
        if not getattr(args, 'no_analyze', False):
            sol_path = os.path.join(folder, "solution.cpp")
            runner_type = "unknown"
            if os.path.exists(sol_path):
                with open(sol_path, 'r') as f:
                    stub = f.read()
                try:
                    ir, _ = run_pipeline_unified(stub)
                    runner_type = ir.runner
                    pjson_path = os.path.join(folder, "problem.json")
                    if os.path.exists(pjson_path):
                        with open(pjson_path, 'r') as f:
                            pdata = json.load(f)
                        pdata["runner"] = ir.runner
                        with open(pjson_path, 'w') as f:
                            json.dump(pdata, f, indent=2)
                except:
                    pass
        
        p_data = {
            "id": int(frontend_id),
            "title": data.get("title", "Unknown"),
            "difficulty": data.get("difficulty", "Unknown")
        }
        
        renderer.emit_success("fetch", p_data, {"folder": folder})
        
    except Exception as e:
        renderer.emit_error("fetch", None, "network", str(e), exit_code=5)

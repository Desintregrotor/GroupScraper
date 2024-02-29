import requests
from urllib.parse import urlencode
import time
from bs4 import BeautifulSoup
import uuid
import re
import json
from flask import session
from flask import Flask, request, redirect, render_template, flash, jsonify
app = Flask(__name__)

def convert_member_count( member_count_str):
    if 'K' in member_count_str:
        return int(float(member_count_str.replace("K members",'')) * 1000)
    elif 'M' in member_count_str:
        return int(float(member_count_str.replace("M members",'')) * 1000000)
    else:
        member_count_str_cleaned = ''.join(filter(str.isdigit, member_count_str))
        return int(member_count_str_cleaned)

def extract_group_info(state):
    components = state.split(' · ')
    if len(components) >= 3:
        privacy_status = components[0]
        member_count = convert_member_count(str(components[1]))
        number_of_posts_text = components[2]
        if 'day' not in number_of_posts_text:
            return None
        number_of_posts = int(re.search(r'\d+', number_of_posts_text).group())
        return privacy_status, member_count, number_of_posts
    else:
        return None
    
    
def get_cookies(email,password):
    headers = {
        'Host': 'www.facebook.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Connection': 'close',
    }

    response = requests.get('https://www.facebook.com/', headers=headers)

    fr=response.cookies['fr']
    sb=response.cookies['sb']
    _datr=response.text.split('"_js_datr","')[1].split('"')[0]
    _token=response.text.split('privacy_mutation_token=')[1].split('"')[0]
    _jago=response.text.split('"jazoest" value="')[1].split('"')[0]
    _lsd=response.text.split('name="lsd" value="')[1].split('"')[0]


    cookies = {
        'fr': fr,
        'sb': sb,
        '_js_datr': _datr,
        'wd': '717x730',
        'dpr': '1.25',
    }

    data = urlencode({
        'jazoest': _jago,
        'lsd': _lsd,
        'email': email,
        'login_source': 'comet_headerless_login',
        'next': '',
        'encpass': f'#PWD_BROWSER:0:{round(time.time())}:{password}',
    })

    headers = {
        'Host': 'www.facebook.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://www.facebook.com/',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': str(len(data)),
        'Origin': 'https://www.facebook.com',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    s = requests.Session()
    response = s.post(f'https://www.facebook.com/login/?privacy_mutation_token={_token}', cookies=cookies, headers=headers, data=data,timeout=30)
    headers = {
        'authority': 'mbasic.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'cache-control': 'max-age=0',
        'dpr': '1.25',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        'sec-ch-ua-full-version-list': '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.71", "Microsoft Edge";v="120.0.2210.61"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'viewport-width': '719',
    }
    if "Check your notifications on another device" not in response.text:
        response = s.post(f'https://mbasic.facebook.com/', headers=headers)
        return response.cookies.get_dict()
    else:
        response_text = response.text
        rev = re.search('{"rev":(.*?)}', str(response_text)).group(1)
        hsi = re.search('"hsi":"(.*?)",', str(response.text)).group(1)
        fb_dtsg = re.search('"async_get_token":"(.*?)"}', str(response_text)).group(1)
        jazoest = re.search('&jazoest=(.*?)",', str(response_text)).group(1)
        lsd = re.search(r'"LSD",\[\],{"token":"(.*?)"', str(response_text)).group(1)
        __spin_r = re.search('"__spin_r":(.*?),', str(response_text)).group(1)
        __spin_t = re.search('"__spin_t":(.*?),', str(response_text)).group(1)
        encryptedContext = re.findall('"entryPointParams":{"encryptedContext":"(.*?)",', str(response_text))[-1]
        haste_session = re.search('"haste_session":"(.*?)",', str(response_text)).group(1)
        while "Check your notifications on another device" in response_text or "PENDING" in response_text:
            time.sleep(5)
            headers3 = {
                'authority': 'www.facebook.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'dpr': '1.25',
                'origin': 'https://www.facebook.com',
                'referer': 'https://www.facebook.com/checkpoint/465803052217681/?next&ct=AWPtrTSF8y4GXaSHmLb-9UxlH9ISKeJI86aFuZcXaXwjfBR7O78jTTt63eIenrfBwAqMPpevdQVArlaoDjB3qri_6DGoK_aMVK9eG7FW5nHhMpr_p862g_n6bfnSBEJ_nIiA06pAtK05jaZmpFf0crnPeEbfzcEDANOPKd_lpK6p66SSKGk3EvbsPM9xn-3PNczO0y8SQtqeoGKqn4oBTKe6-W_HB7JcC-F-M_KAsY-AYathY3WYybnjfMo7vbRuy6pcvKTZm1U_vjqEzO_t-CZAMD_SUTb2dlYRNjmQ1DxwMtJkk75QGc9oFAOpWoxHGFnhRyKDoegrRJSqsxDlFwXmPVnI_V2IU02rXV2VNq9bb-Rx-y9YMx4pfYlks59SrJ6yFPji0LgAF38nlZKaSUDSgTo',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
                'sec-ch-ua-full-version-list': '"Chromium";v="122.0.6261.70", "Not(A:Brand";v="24.0.0.0", "Microsoft Edge";v="122.0.2365.59"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"15.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
                'viewport-width': '934',
                'x-asbd-id': '129477',
                'x-fb-friendly-name': 'TwoStepVerificationUpdateLoginMutation',
                'x-fb-lsd': lsd,
            }
            data = {'av': '0','__user': '0','__a': '1','__req': 'x','__hs': haste_session,'dpr': '1.5','__ccg': 'GOOD','__rev': rev,'__s': 'xripyu:bgv88y:6y755o','__hsi': hsi,'__comet_req': '15','fb_dtsg': fb_dtsg,'jazoest': jazoest,'lsd': lsd,'__spin_r': __spin_r,'__spin_b': 'trunk','__spin_t': __spin_t,'fb_api_caller_class': 'RelayModern','fb_api_req_friendly_name': 'TwoStepVerificationUpdateLoginMutation','variables': '{"encrypted_context":"'+encryptedContext+'"}','server_timestamps': 'true','doc_id': '6812650572129819',}
            response_text = s.post('https://www.facebook.com/api/graphql/', cookies=cookies, headers=headers3, data=data).text
        response = s.post(f'https://mbasic.facebook.com/', headers=headers)
        return response.cookies.get_dict()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    cookies = get_cookies(email, password)
    if "c_user" in cookies:
        session['cookies'] = cookies  # Store cookies in session
        return redirect('/input_data')
    else:
        flash("فشل تسجيل الدخول")
        return redirect('/')

@app.route('/input_data')
def input_data():
    return render_template('input_data.html')

@app.route('/scrape_groups', methods=['POST'])
def scrape_groups():
    cookies = session.get('cookies')
    group_data = []
    keyword = request.form['keyword']
    count = request.form['count']
    min_member_count = int(request.form['min_member_count'])
    min_posts_per_day = int(request.form['min_posts_count'])
    group_status = request.form['group_status']
    headers = {
        'authority': 'www.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'dpr': '1.25',
        'referer': 'https://www.google.com/',
        'sec-ch-prefers-color-scheme': 'light',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-full-version-list': '"Chromium";v="122.0.6261.70", "Not(A:Brand";v="24.0.0.0", "Google Chrome";v="122.0.6261.70"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'viewport-width': '1155',
    }
    params = {
        'q': keyword,
        'locale': 'ar_AR',
    }
    response = requests.get('https://www.facebook.com/search/groups/',headers=headers,params=params, cookies=cookies)
    response_text = response.text

    ids = re.findall('"tapped_result_id":"(.*?)"', response_text)
    names = re.findall('"__typename":"Group","name":"(.*?),"id"', response_text)
    status = re.findall('"primary_snippet_text_with_entities":(.*?),"description_snippets_text_with_entities":', response_text)

    # Print the information for each group
    for group_id ,group_name ,group_status in zip(ids, names, status):
        if "since" in group_status or "unread" in group_status or "Recently" in group_status:
            continue
        group_info = extract_group_info(json.loads(group_status)['text'])
        if group_info is None:
            continue
        privacy_status, member_count, number_of_posts = group_info

        if member_count >= min_member_count and number_of_posts >= min_posts_per_day:
            group_data.append({
                'id': group_id,
                'name': group_name,
                'privacy_status': privacy_status,
                'member_count': member_count,
                'number_of_posts': number_of_posts,
                'url': f"https://www.facebook.com/groups/{group_id}"
            })


    rev = re.search('{"rev":(.*?)}', str(response_text)).group(1)
    hsi = re.search('"hsi":"(.*?)",', str(response_text)).group(1)
    fb_dtsg = re.search('"DTSGInitialData":{"token":"(.*?)"', str(response_text)).group(1)
    jazoest = re.search('&jazoest=(.*?)",', str(response_text)).group(1)
    lsd = re.search('"LSD",\[\],{"token":"(.*?)"', str(response_text)).group(1)
    __spin_r = re.search('"__spin_r":(.*?),', str(response_text)).group(1)
    __spin_t = re.search('"__spin_t":(.*?),', str(response_text)).group(1)
    next_page_id = re.findall('"page_info":{"has_next_page":true,"end_cursor":"(.*?)"}', str(response_text))[-1]

    c_user_value = re.search('__user=(.*?)&', str(response_text)).group(1)
    haste_session = re.search('"haste_session":"(.*?)",', str(response_text)).group(1)
    new_headers = {
        'x-fb-friendly-name': 'SearchCometResultsPaginatedResultsQuery',
        'x-fb-lsd': lsd,
    }
    headers.update(new_headers)
    while len(group_data) < int(count):
        data = {
            'av': c_user_value,
            '__aaid': '0',
            '__user': c_user_value,
            '__a': '1',
            '__req': '5r',
            '__hs': haste_session,
            'dpr': '1.5',
            '__ccg': 'GOOD',
            '__rev': rev,
            '__hsi': hsi,
            '__comet_req': '15',
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest,
            'lsd': lsd,
            '__spin_r': __spin_r,
            '__spin_b': 'trunk',
            '__spin_t': __spin_t,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'SearchCometResultsPaginatedResultsQuery',
            'variables': '{"allow_streaming":false,"args":{"callsite":"COMET_GLOBAL_SEARCH","config":{"exact_match":false,"high_confidence_config":null,"intercept_config":null,"sts_disambiguation":null,"watch_config":null},"context":{"bsid":"' + str(uuid.uuid4()) + '","tsid":null},"experience":{"encoded_server_defined_params":null,"fbid":null,"type":"GROUPS_TAB"},"filters":[],"text":"'+ keyword +'"},"count":5,"cursor":"' + next_page_id + '","feedLocation":"SEARCH","feedbackSource":23,"fetch_filters":true,"focusCommentID":null,"locale":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"search_results_page","scale":1.5,"stream_initial_count":0,"useDefaultActor":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
            'server_timestamps': 'true',
            'doc_id': '7221046597980736',
        }

        response = requests.post('https://www.facebook.com/api/graphql/', data=data,headers=headers,timeout=120,cookies=cookies).json()

        groups = response["data"]["serpResponse"]["results"]["edges"]
        for group in groups:
            group_status = group["relay_rendering_strategy"]["view_model"]["primary_snippet_text_with_entities"]["text"]
            if "since" in group_status or "unread" in group_status or "Recently" in group_status:
                continue
            group_info = extract_group_info(group_status)
            if group_info is None:
                continue
            privacy_status, member_count, number_of_posts = group_info

            group_id = group["relay_rendering_strategy"]["view_model"]["profile"]["id"]
            group_name = group["relay_rendering_strategy"]["view_model"]["profile"]["name"]

            if member_count >= min_member_count and number_of_posts >= min_posts_per_day:
                group_data.append({
                    'id': group_id,
                    'name': group_name,
                    'privacy_status': privacy_status,
                    'member_count': member_count,
                    'number_of_posts': number_of_posts,
                    'url': f"https://www.facebook.com/groups/{group_id}"
                })
        next_page_id = response["data"]["serpResponse"]["results"]["page_info"]["end_cursor"]
        if not next_page_id:
            break
    return render_template('preview_groups.html', groups=group_data)

@app.route('/join_group', methods=['POST'])
def join_group():
    headers = {
        'authority': 'mbasic.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'cache-control': 'max-age=0',
        'dpr': '1.25',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        'sec-ch-ua-full-version-list': '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.71", "Microsoft Edge";v="120.0.2210.61"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'viewport-width': '719',
    }
    cookies = session.get('cookies')
    group_url = request.form['group_url']
    response = requests.get(group_url.replace("www",'mbasic') ,cookies=cookies, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html5lib')
        try:
            join_url = soup.select_one('form[action^="/a/group/join/"]')["action"]
            if join_url:
                response = requests.get(f"https://mbasic.facebook.com{join_url}" ,cookies=cookies, headers=headers)
                if response.status_code == 200:
                    return jsonify({'message': 'Group joined successfully'})
        except:
            return jsonify({'message': 'Already Member'})
    return jsonify({'error': 'Failed to join the group'})
if __name__ == '__main__':
    app.secret_key = 'Refoo'  # Set a secret key for session management
    app.run(debug=True)

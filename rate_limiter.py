import time
import threading
from threading import Lock

ip_requests={}
user_requests={}
requests_lock=Lock()

def _cleanup_old_entries():
    global ip_requests,user_requests
    while True:
        time.sleep(60)
        with requests_lock:
            current_time=time.time()
            cutoff_time=current_time-3600
            ip_requests={ip:[ts for ts in timestamps if ts>cutoff_time] for ip,timestamps in ip_requests.items() if timestamps}
            user_requests={key:[ts for ts in timestamps if ts>cutoff_time] for key,timestamps in user_requests.items() if timestamps}
            ip_requests={k:v for k,v in ip_requests.items() if v}
            user_requests={k:v for k,v in user_requests.items() if v}

cleanup_thread=threading.Thread(target=_cleanup_old_entries,daemon=True)
cleanup_thread.start()

def check_ip_rate_limit(ip,key,limit,window_seconds):
    global ip_requests
    current_time=time.time()
    cutoff_time=current_time-window_seconds
    full_key=f"{ip}:{key}"
    with requests_lock:
        if full_key not in ip_requests:
            ip_requests[full_key]=[]
        ip_requests[full_key]=[ts for ts in ip_requests[full_key] if ts>cutoff_time]
        if len(ip_requests[full_key])<limit:
            ip_requests[full_key].append(current_time)
            return True,0
        retry_after=int(ip_requests[full_key][0]+window_seconds-current_time)+1
        return False,retry_after

def check_user_rate_limit(user_id,key,limit,window_seconds):
    global user_requests
    current_time=time.time()
    cutoff_time=current_time-window_seconds
    full_key=f"{user_id}:{key}"
    with requests_lock:
        if full_key not in user_requests:
            user_requests[full_key]=[]
        user_requests[full_key]=[ts for ts in user_requests[full_key] if ts>cutoff_time]
        if len(user_requests[full_key])<limit:
            user_requests[full_key].append(current_time)
            return True,0
        retry_after=int(user_requests[full_key][0]+window_seconds-current_time)+1
        return False,retry_after

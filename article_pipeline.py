import time
import redis
from Cluster.cluster_articles import cluster
from Fetcher.scraper import run_scraper
from Summarizer import summarize

import config
from database.db_engine import SessionLocal
from database.db_models import Article, Summary
from CelerySummarizer.tasks import summarize_cluster
from celery.result import AsyncResult
from config import SUMMARY_REDIS_IP_ADDRESS, SUMMARY_REDIS_PASSWORD, SUMMARY_REDIS_PORT

from celery import Celery
import logging
import schedule

"""
PIPELINE FOR PERIODIC 
FETCHING -> CLUSTERING -> INIT SUMMARY DB -> QUEUING FOR SUMMARIZATION -> CLEANING COMPLETE TASKS
"""

if config.REMOTE_HOST:
    print("remote host")
    r = redis.Redis(host=SUMMARY_REDIS_IP_ADDRESS, port=SUMMARY_REDIS_PORT, password=SUMMARY_REDIS_PASSWORD)
    app = Celery("Celery_Summarizer", broker=f"redis://:{config.SUMMARY_REDIS_PASSWORD}@{config.SUMMARY_REDIS_IP_ADDRESS}:{config.SUMMARY_REDIS_PORT}/0")
else:
    r = redis.Redis(host=SUMMARY_REDIS_IP_ADDRESS, port=SUMMARY_REDIS_PORT)
    app = Celery("Celery_Summarizer", broker=f"redis://{config.SUMMARY_REDIS_IP_ADDRESS}:{config.SUMMARY_REDIS_PORT}/0")

def add_to_queue(cluster_id):
    if r.sismember("summarization_tasks", cluster_id):
        print(f"Task for cluster {cluster_id} is already in progress.")
        return
    
    task = summarize_cluster.delay(cluster_id)
    r.sadd("summarization_tasks",cluster_id)
    r.set(f"task_id:{cluster_id}", task.id)
    print(f"Task for cluster {cluster_id} added to queue with task id {task.id}")
    return task.id

def check_and_remove_completed_tasks():
    for cluster_id in r.smembers("summarization_tasks"):
        task_id = r.get(f"task_id:{cluster_id}")
        
        if task_id is None:
            print(f"Task ID for cluster {cluster_id} is None. Skipping.")
            continue
        task_result = AsyncResult(task_id)
        if task_result.state == "SUCCESS" or task_result.state == "FAILURE":
            r.srem("summarization_tasks", cluster_id)
            r.delete(f"task_id:{cluster_id}")
            print(f"Task for cluster {cluster_id} has finished and removed from the queue.")
        else:
            print(f"Task for cluster {cluster_id} is still in progress.")

def pipeline():
    db = SessionLocal()
    print("Started running scraper..")
    run_scraper()
    print("Done scraping.")
    print("Started clutering articles..")
    cluster()
    print("Done Clustering")
    print("Initializing summary DB with unsummarized articles..")
    summarize.init_summary_db()
    print("Done initializing database with summaries.")
    print("Queuing data for summary")

    pending_summaries = db.query(Summary).filter(Summary.summary==None).all()
    for pending_summary in pending_summaries:
        add_to_queue(pending_summary.cluster_id)
    db.close()
    print("Successfully Queued")
    check_and_remove_completed_tasks()
    

def main():
    # pipeline() #-->run onlt one time
    #Runs every X minutes->
    schedule.every(config.DEFAULT_SCRAPE_TTL).minutes.do(pipeline)

    print(f"Scheduler Started. Running every {config.DEFAULT_SCRAPE_TTL} minutes")
    while True:
        schedule.run_pending()
        time.sleep(1)

    
if __name__ == '__main__':
    main()
    # celery -A Celery_Summarizer.tasks worker --pool=solo


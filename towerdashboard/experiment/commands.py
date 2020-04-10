import click
import jenkins
import requests
from functools import partial

from flask import current_app

from towerdashboard.models import TestRun

from . import experiment


@experiment.cli.command('crawl_jenkins_jobs')
@click.argument('job_name', default='Test_Tower_Yolo_Express', required=False)
def crawl_jenkins_jobs(job_name):
    app = current_app
    JOB_NAME = job_name

    def get_results(server, build_id, base_url, artifact_path):
        url = base_url + '/artifact/' + artifact_path

        request = requests.Request(method='POST', url=url)
        res = server.jenkins_request(request)
        return res.content.decode('utf-8')

    server = jenkins.Jenkins(app.config['JENKINS_URL'],
                             username=app.config['JENKINS_USERNAME'],
                             password=app.config['JENKINS_TOKEN'])

    builds = server.get_job_info(JOB_NAME)['builds']
    for b in builds:
        build_number = b['number']
        build_details = server.get_build_info(JOB_NAME, build_number, depth=2)

        '''
        Structure for build matrix
        '''
        #for r in build_details['runs']:
        params = {}
        params_found = False
        for build_detail in build_details['actions']:
            if 'parameters' in build_detail:
                for p in build_detail['parameters']:
                    params[p['name']] = p['value']
                params_found = True
                break

        if params_found is False:
            app.logger.warn(f"Parameters not found for {build_details['fullDisplayName']}")
        else:
            app.logger.info(f"Parameters found for {build_details['fullDisplayName']}")

        for v in ['fullDisplayName', 'id', 'result', 'duration', 'estimatedDuration', 'building', 'queueId']:
            params[v] = build_details[v]

        for a in build_details['artifacts']:
            if a['fileName'] == 'results.xml':
                results_xml = get_results(server, build_details['id'], build_details['url'], a['relativePath'])
                d = {
                    'data': results_xml,
                    'run': {
                        'params': params,
                    }
                }
                res = requests.post('http://web:80/jenkins/import/', json=d)
                print(res.json())
                break


@experiment.cli.command('crawl_jenkins_pipeline')
def crawl_jenkins_pipeline(pipeline_name='integration-pipeline'):
    app = current_app

    class Jenkins():
        def __init__(self, base_url, username, token):
            self.s = requests.Session()
            self.s.auth = (username, token)
            self.s.headers.update({'Accept': 'application/json'})

            def new_request(prefix, f, method, url, *args, **kwargs):
                if url.startswith('http'):
                    return f(method, url, *args, **kwargs)
                else:
                    return f(method, prefix + url, *args, **kwargs)

            self.s.request = partial(new_request, base_url.rstrip('/') + '/', self.s.request)

    cli = Jenkins(app.config['JENKINS_URL'],
                  app.config['JENKINS_USERNAME'],
                  app.config['JENKINS_TOKEN'])

    res = cli.s.get(f'/job/Pipelines/job/{pipeline_name}/api/json?pretty=true')
    builds = res.json()['builds']
    for b in builds:
        build_number = b['number']
        build_details = cli.s.get(f"{b['url']}api/json", params={"depth": 2}).json()

        params = {}
        params_found = False
        for build_detail in build_details['actions']:
            if 'parameters' in build_detail:
                for p in build_detail['parameters']:
                    params[p['name']] = p['value']
                params_found = True
                break

        if params_found is False:
            app.logger.warn(f"Parameters not found for {build_details['fullDisplayName']}")
        else:
            app.logger.info(f"Parameters found for {build_details['fullDisplayName']}")

        for v in ['fullDisplayName', 'id', 'result', 'duration', 'estimatedDuration', 'building', 'queueId']:
            params[v] = build_details[v]

        for a in build_details['artifacts']:
            if a['fileName'] == 'results.xml':
                url = f"{build_details['url']}artifact/{a['relativePath']}"
                res = cli.s.get(url)
                test_results = res.content.decode("utf-8")
                d = {
                    'data': test_results,
                    'run': {
                        'params': params,
                    }
                }
                res = requests.post('http://web:80/jenkins/import/', json=d)
                break


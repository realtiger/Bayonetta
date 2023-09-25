import httpx
import yaml


class KubeService:
    def __init__(self, kube_config: str = None):
        # 定义变量
        self.cluster = None
        self.user = None
        cluster = None
        user = None

        # 读取kube config
        conf = yaml.safe_load(kube_config)
        # 获取当前上下文
        current_context = conf.get('current-context')

        if current_context is None:
            raise ValueError("kube config is invalid, current-context is None")

        # 获取所有的上下文
        contexts = conf.get('contexts')
        if contexts is None or not isinstance(contexts, list) or len(contexts) == 0:
            raise ValueError("kube config is invalid, contexts is None or not list or len(contexts) == 0")

        # 获取当前上下文的cluster和user
        for context in contexts:
            if context.get('name') == current_context:
                cluster = context.get('context').get('cluster')
                user = context.get('context').get('user')
                break

        # 获取所有的cluster
        clusters = conf.get('clusters')
        if clusters is None or not isinstance(clusters, list) or len(clusters) == 0:
            raise ValueError("kube config is invalid, clusters is None or not list or len(clusters) == 0")

        # 获取当前cluster
        for cluster_item in clusters:
            if cluster_item.get('name') == cluster:
                self.cluster = cluster_item.get('cluster')
                break

        # 获取所有的user
        users = conf.get('users')
        if users is None or not isinstance(users, list) or len(users) == 0:
            raise ValueError("kube config is invalid, users is None or not list or len(users) == 0")

        # 获取当前user
        for user_item in users:
            if user_item.get('name') == user:
                self.user = user_item.get('user')
                break

        self.host = self.cluster.get('server').rstrip('/')
        self.token = f'Bearer {self.user.get("token")}'

    async def request(
            self,
            method: str,
            url: str,
            allow_watch_bookmarks: bool = None,
            _continue=None,
            field_selector=None,
            label_selector=None,
            limit=None,
            pretty=None,
            resource_version=None,
            resource_version_match=None,
            send_initial_events=None,
            timeout_seconds=None,
            watch=None,
            **kwargs
    ):
        # header参数
        headers = {'Accept': 'application/json', 'authorization': self.token}
        # query参数
        query_params = {}

        if allow_watch_bookmarks is not None:
            query_params['allowWatchBookmarks'] = allow_watch_bookmarks
        if _continue is not None:
            query_params['continue'] = _continue
        if field_selector is not None:
            query_params['fieldSelector'] = field_selector
        if label_selector is not None:
            query_params['labelSelector'] = label_selector
        if limit is not None:
            query_params['limit'] = limit
        if pretty is not None:
            query_params['pretty'] = pretty
        if resource_version is not None:
            query_params['resourceVersion'] = resource_version
        if resource_version_match is not None:
            query_params['resourceVersionMatch'] = resource_version_match
        if send_initial_events is not None:
            query_params['sendInitialEvents'] = send_initial_events
        if timeout_seconds is not None:
            query_params['timeoutSeconds'] = timeout_seconds
        if watch is not None:
            query_params['watch'] = watch

        async with httpx.AsyncClient(verify=False) as client:
            match method:
                case 'GET' | 'get':
                    response = await client.get(url, headers=headers, params=query_params)
                case 'POST' | 'post':
                    response = await client.post(url, headers=headers, params=query_params)
                case 'PUT' | 'put':
                    response = await client.put(url, headers=headers, params=query_params)
                case 'DELETE' | 'delete':
                    response = await client.delete(url, headers=headers, params=query_params)
                case 'PATCH' | 'patch':
                    response = await client.patch(url, headers=headers, params=query_params)
                case _:
                    raise ValueError(f"method {method} is not supported")

        return response

    async def list_namespace(self, **kwargs):
        url = f'{self.host}/api/v1/namespaces'
        response = await self.request('get', url)

        return response.json()

    async def list_namespaced_deployment(self, namespace, **kwargs):
        url = f'{self.host}/apis/apps/v1/namespaces/{namespace}/deployments'
        response = await self.request('get', url, *kwargs)

        return response.json()

    async def list_pod_for_all_namespaces(self, **kwargs):
        # 访问路径参数
        url = f'{self.host}/api/v1/pods'
        response = await self.request('get', url, **kwargs)

        return response.json()

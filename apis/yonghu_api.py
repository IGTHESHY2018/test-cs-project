from apis.base_api import BaseApi

class YonghuApi(BaseApi):
    resource = "/yonghu"

    def register(self,payload:dict):
        """注册，POST JSON body。"""
        return self.client.post(self._path("register"), json=payload)
    
    def session(self):
        """获取当前登录用户信息，GET /yonghu/session"""
        return self.client.get(self._path("session"))
      
    def logout(self):
        """注销登录，POST /yonghu/logout"""
        return self.client.get(self._path("logout"))
    
    def reset_pass(self,username:str):
        """重置密码，POST /yonghu/resetPass"""
        return self.client.get(self._path("resetPass"),params={"username":username})

    def detail(self,id):
        return self.client.get(self._path("detail") + f"/{id}")
    
    def add(self,payload:dict):
        return self.client.post(self._path("add"),json=payload)
    
    def login(self, username: str, password: str):
        """用户登录，POST /users/login?username=&password=，@IgnoreAuth 免登录 返回完整 R 响应 dict（含 token 字段）"""
        return self.client.post(self._path("login"), params={"username": username, "password": password})


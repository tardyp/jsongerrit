import jsonrpclib
from closedstats import closedstats

gerrit_server = "https://review.source.android.com/gerrit"
class Gerrit():
    def __getattr__(self,name):
        proxy= jsonrpclib.ServerProxy("%s/rpc/%s"%(gerrit_server,name))
        self.__dict__[name]=proxy
        return proxy


if __name__ == "__main__":
    gerrit = Gerrit()
    closedstats(gerrit)
    

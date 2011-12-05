class UniqueId(object):
    def __init__(self):
        self.index = 0
    def getId(self):
        self.index += 1
        return self.index 

def uniqueIdFunc():
    uid_obj = UniqueId()
    def giveId():
        return uid_obj.getId()
    return giveId

uniqueGlListId = uniqueIdFunc()


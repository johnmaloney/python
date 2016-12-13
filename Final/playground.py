from collections import namedtuple 

header = namedtuple("Header", "Id, Name")

headers = [header("1", "One"), header("2", "Two")]

print(any(h.Id=="1" for h in headers))

print([h.Name for h in headers if h.Id == "2"][0])


print 1

test = "one|two|three".split("|")


test ="test ".lstrip()
#test = "cdba".rsort()
#test = "test  t".zfill()

myList = [1, 2, "cookie jar", [64, "crumbs"], 51094]

colorList = ["Red", "Green", ["Navy", "Cornflower", "Teal"], "Yellow"]
test = "john".capitalize()
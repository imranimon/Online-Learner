def process_list(result):
    process_result = []
    if result is not None:
        for item in result:
            k=list(item)
            process_result.append(k)
        return process_result
    else:
        return process_result

def check_availabe(course,enrolled):
    available=[]
    for i in course:
        for j in enrolled:
            if i[3]==j[0]:
                i[1]=i[1]-j[1]
    for i in course:
        if i[1]>0:
            available.append(i)
    return available
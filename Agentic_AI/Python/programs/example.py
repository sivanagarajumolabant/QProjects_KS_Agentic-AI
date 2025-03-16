lis = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12,13]

sub_lis = []
final_list =[]
count = 0
length = 4

for li in range(0,len(lis)):
    sub_lis.append(lis[li])
    count+=1
    if len(sub_lis)==length:
        final_list.append(sub_lis)
        sub_lis=[]
        count=0
if sub_lis:
    final_list.append(sub_lis)
    
print(final_list)
import os
import re
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.models import auth, User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from common_func.django_user_func import get_paginated_list, save_file
from common_func.custom_log import Custom_Log

from .models import DBUpdate
from .dbupdate_tmobile import dbupdate_tmobile
from .dbupdate_vz import dbupdate_vz
from django.views.decorators.csrf import csrf_exempt


def check_superuser(user): return user.is_superuser

import requests


@login_required(login_url='/login/')
def home(request): return render(request, 'index.html', {})


def login(request):
    if request.method == 'POST':
        user = auth.authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            user = User.objects.get(username=user.username)
            auth.login(request, user)
            request.session.set_expiry(4 * 60 * 60)
            return redirect('/')
        else:
            messages.info(request, 'Invalid User name or Password !!!')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')


@login_required(login_url='/login/')
def logout(request):
    # send_notification_mail(request.user, 'Logout')
    request.session['auth_status'] = 'not_authenticated'
    request.session['otp_status'] = 'not_verified'
    auth.logout(request)
    return redirect('/')


@login_required(login_url='/login/')
@user_passes_test(check_superuser, login_url='/')
def dbupdate(request):
    if request.method == 'POST':
        appname = request.POST.get('appname')
        remark = request.POST.get('remark')
        user = User.objects.get(username=request.user.username)
        job = DBUpdate.objects.create(appname=appname, remark=remark, user=user)
        job.save()
        curr_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
        _, dbupdate_file = save_file(request, 'dbupdate_file', curr_datetime, location=appname, activity='dbupdate')
        log_file = os.path.join(settings.MEDIA_ROOT, 'dbupdate', F'dbupdate_{datetime.now().strftime("%Y%m%d%H%M%S")}.log')
        custom_log = Custom_Log(log_file=log_file, activity=F'Updating DB Tables for {appname} ')

        job.status = 'Running'
        job.save()
        act_flag = False
        if appname == 'tmobile': act_flag = dbupdate_tmobile(dbupdate_file, custom_log)
        elif appname == 'vz': act_flag = dbupdate_vz(dbupdate_file, custom_log)
        if act_flag:
            custom_log.log.info(F'Status: Successful!!!')
            custom_log.log.info(F'Job completed for Updating DB Tables : {appname}, Status: Successful!!!')
            job.status = 'Completed'
        else:
            custom_log.log.info(F'Status: Failed!!!')
            custom_log.log.info(F'Job completed for Updating DB Tables : {appname}, Status: Failed!!!')
            job.status = 'Failed'
        custom_log.release()
        job.script = os.path.basename(log_file)
        job.save()
        return HttpResponseRedirect('/dbupdatelist/')
    return render(request, 'dbupdate.html', {'appname': ['tmobile', 'vz']})


@login_required(login_url='/login/')
@user_passes_test(check_superuser, login_url='/')
def dbupdatelist(request):
    jobs = DBUpdate.objects.all()
    jobs = get_paginated_list(request, jobs)
    return render(request, 'dbupdatelist.html', {'jobs': jobs})





def autologin(request,token):
    # if request.method == 'GET':
    print(token,'gggg')
    if(token!=None):
        print("jnsdclkjwbhdckdsv",token)
        headers = {
            'User-Agent': 'My Custom User Agent',
            'Authorization': 'Bearer '+token
        }
        response = requests.get("https://ssodevapi.mpulsenet.com/getDetail", headers=headers) 
        #response = requests.get("http://127.0.0.1:8090/getDetail", headers=headers) 
        print("hbjhbjhbjhbjh",response.json())
        tempKey=response.json()
        # user='sandeep'
        sendData={}
        # print("ckjbckjebhvhkfver=",sendData)
        sendData["idToken"]=token
        # sendData={**sendData,**tempKey["userDetails"]}
        print(tempKey)
        print("sendData",tempKey["userDetails"])

        ussr=tempKey["userDetails"]
        print('jjjjjpankaj',ussr['email'])

        # user=ussr["email"]
        request.session['auth_otp'] = '2345'
        request.session['auth_status'] = 'authenticated'
        request.session['otp_status'] = 'verified'
        request.session['auth_status_user'] = ussr["email"]
        # request.session['group'] = tempKey["userDetails"]["department"]["values"]
        
        user = User.objects.get(email=ussr["email"])
        
        # my_group = Group.objects.get(name='tmobile')
        # my_group2 = Group.objects.get(name='attgsaudit')
        # my_group3 = Group.objects.get(name='attscripter')
        # print(user,"my_group",my_group,my_group2,my_group3)
        # my_group.user_set.add(user)
        # my_group2.user_set.add(user)
        # my_group3.user_set.add(user)
        auth.login(request, user)
        request.session.set_expiry(4 * 60 * 60)
        return redirect('/')
    return HttpResponse({token})


@csrf_exempt
def create_user(request):
    print(request.method,request.POST)
    if request.method == 'POST': 
        username = request.POST['email']
        password = request.POST['password']
        print('kkkkk',request.POST)
        email = request.POST["email"]
        is_superuser = True if request.POST["is_superuser"]=="Granted" else False
        # group = request.POST['group']
        # group=group.split(",")
        # print(group,"groupgroup")
        if User.objects.filter(username=username,email=email).exists():
            return HttpResponse("Username already exists.")

        
        pawan=username.split(" ")
        if len(pawan)>2:
            first_name=pawan[0]+pawan[1]
            last_name=pawan[-1]
        else:
            first_name=pawan[0]
            last_name=pawan[-1]

        print("1169")
        
        user = User.objects.create_user(username=username, password=password,first_name=first_name,last_name=last_name,email=email,is_superuser=is_superuser,is_staff=is_superuser)
        # auth.login(request, user)

        print("1174")

        # try:
                
        #     for i in group:
        #         my_group = Group.objects.get(name=i)
        #         print(my_group,user)
        #         print('kkkklll')
        #         my_group.user_set.add(user)
        #         print(my_group,user)
        # except Exception as e:
        #     print(e)

        

        return HttpResponse("Successfully add user.")


        # last_login=request.POST['last_login']
        # is_superuser=request.POST['is_superuser']
        # first_name=request.POST['first_name']
        # last_name=request.POST['last_name']
        # emai=request.POST['email']
        # is_staff=request.POST['is_staff']
        # is_active=request.POST['is_active']
        # date_joined=request.POST['date_joined']

        # form_data = {
        #     'username': username,
        #     'password': password,
        #     # 'last_login':last_login,
        #     # 'is_superuser':is_superuser,
        #     # 'first_name':first_name,
        #     # 'last_name':last_name,
        #     # 'emai':emai,
        #     # 'is_staff':is_staff,
        #     # 'is_active':is_active,
        #     # 'date_joined':date_joined
        # }
        # user = auth.authenticate(request, username=username, password=password)
        # print(user,'ggggg')
        # return redirect( '/')    
    else:
        # request.session['auth_status'] = 'not_authenticated'
        # request.session['otp_status'] = 'not_verified'
        return render(request, 'login.html')

@csrf_exempt
def edit_user(request):
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        group = data.get('group')
        grouper = group.split(",")
        mobile = data.get('mobile')
        reader=[]
        try:
            print("dsadsadsadsadsadsa")
            user = User.objects.get(email=email)
            user_groups = user.groups.all()
            print(user_groups)
            for group in user_groups:
                reader.append(group.name)
                if(group.name not in grouper):
                    user.groups.remove(group.id)
            for i in grouper:
                if(i not in reader):
                    my_group = Group.objects.get(name=i)
                    my_group.user_set.add(user)
                    print('all users and groupsssss',my_group,user)
            # return JsonResponse({'Successfully': 'User created'}, status=200)
            return JsonResponse({'Successfully': 'User created'}, status=200)
            # for i in grouper:
            #     if(i not in reader):
            #         my_group = Group.objects.get(name=i)
            #         print(my_group)
            #         my_group.user_set.add(user)

            # for i in grouper:
            #     if(i not in reader):
            #         my_group = Group.objects.get(name=i)
            #         my_group.user_set.add(user)
            # for i in grouper:
            #     is_in_group = user.groups.all()
            #     print(is_in_group) 
            #     if(is_in_group):
            #         user.groups.remove(my_group)


            # for i in group.split(","):
            #     my_group = Group.objects.get(name=i)
            #     is_in_group = user.groups.filter(name=my_group.name).exists()
            #     if(is_in_group):
            #         user.groups.remove(my_group)

                    
            # if mobile:
            #     user.mobile = mobile
            try:
                user.full_clean()
                user.save()
                return JsonResponse({'message': 'User information updated successfully'})
            except ValidationError as e:
                return JsonResponse({'error': f'Validation Error: {e}'}, status=400)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=405)



@csrf_exempt
def autodelete(request):
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        try:
            user = User.objects.get(email=email)
            user.delete()
            return JsonResponse({'message': 'User deleted successfully'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def users_with_groups(request):
    if request.method == 'GET':
        users = User.objects.all()
        serialized_users = serializers.serialize('json', users, use_natural_foreign_keys=True)
        user_data = json.loads(serialized_users)
        print('kk')
        print(user_data)
        print('jjj')
                
        users_with_groups = []
        for item in user_data:
            user_info = item['fields']
            user_info['groups'] = item['fields']['groups']
            users_with_groups.append(user_info)
        print(users_with_groups)
        return JsonResponse({'users_with_groups': users_with_groups}, safe=False)
# def update_api(request):
#     users = User.objects.all()
#     email_list = [user.email for user in users]
#     print('all emails list',email_list)

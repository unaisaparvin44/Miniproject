from datetime import datetime, timezone
from email import message
from math import prod
from unicodedata import category
from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
import random
import math
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        try:
            auctionuser = AuctionUser.objects.get(user=request.user)
            if auctionuser.status == "pending":
                messages.success(request, "Your verification is pending. Complete your additional details and email verification. If already completed, try logging in later.")
                return redirect('profile', request.user.id)
        except  AuctionUser.DoesNotExist:
            messages.error(request, "You do not have an AuctionUser profile. Please complete registration.")
            return redirect('signup')  # Redirect to the signup page or appropriate page

    upcoming_product = Product.objects.filter(status="upcoming")
    closed_product = Product.objects.filter(status="closed")
    live_product = Product.objects.filter(status="live")
    d = {'upcoming_product':upcoming_product, 'closed_product':closed_product, 'live_product':live_product}
    return render(request, 'home.html', d)

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('fname', '').strip()
        last_name = request.POST.get('lname', '').strip()
        username = request.POST.get('uname', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('pwd')
        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('add', '').strip()
        dob = request.POST.get('dob')
        user_type = request.POST.get('reg')
        agreed = request.POST.get('chkChecked')
        image = request.FILES.get('image')

        errors = {}
        # Required field validation
        if not first_name:
            errors['fname'] = 'First name is required.'
        if not last_name:
            errors['lname'] = 'Last name is required.'
        if not username:
            errors['uname'] = 'Username is required.'
        if not email:
            errors['email'] = 'Email is required.'
        if not password:
            errors['pwd'] = 'Password is required.'
        if not user_type:
            errors['reg'] = 'Please choose a user type.'
        if not agreed:
            errors['chkChecked'] = 'You must accept the Terms and Privacy Policy.'

        # Simple format validations
        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = 'Enter a valid email address.'
        if username and (len(username) < 3 or len(username) > 30):
            errors['uname'] = 'Username must be 3-30 characters.'
        if password and len(password) < 6:
            errors['pwd'] = 'Password must be at least 6 characters.'
        if contact:
            if not contact.isdigit() or len(contact) != 10:
                errors['contact'] = 'Contact must be a 10-digit number.'

        if errors:
            ctx = {'errors': errors, 'form': request.POST}
            return render(request, 'signup.html', ctx)

        try:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
        except IntegrityError:
            messages.error(request, "Username already taken. Please choose another.")
            return render(request, 'signup.html', {'form': request.POST})

        mem = Member_fee.objects.filter(fee__iexact="Unpaid").first()
        auction_user_kwargs = {
            'membership': mem,
            'user': user,
            'contact': contact,
            'address': address,
            'user_type': user_type,
            'agree': True,
        }
        if dob:
            auction_user_kwargs['dob'] = dob
        if image:
            auction_user_kwargs['image'] = image
        AuctionUser.objects.create(**auction_user_kwargs)
        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')
    return render(request, 'signup.html')

def Logout(request):
    logout(request)
    return redirect('home')

def login_user(request):
    if request.method == "POST":
        u = request.POST['uname']
        p = request.POST['pwd']
        user = authenticate(username=u, password=p)
        sign = ""
        if user and not user.is_staff:
            login(request, user)
            messages.success(request, "Logged in Successfully")
            return redirect('home')
        else:
            messages.success(request, "Invalid credential")
    return render(request, 'login.html')


def Add_Product(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    cat = Category.objects.all()
    scat = Sub_Category.objects.all()
    sell = AuctionUser.objects.get(user=request.user)
    if request.method == "POST":
        c = request.POST['cat']
        s = request.POST.get('scat')
        if not s:
            messages.error(request, "Please select a sub-category.")
            return render(request, 'add_product.html', {'cat': cat, 'scat': scat})
        p = request.POST['p_name']
        pr = request.POST['price']
        im = request.FILES['image']
        start = request.POST['start']
        end = request.POST['interval_price']
        desc = request.POST['desc']
        bid_type = request.POST['bid_type']
        # Safely parse number of parts; default to 0 if missing/blank
        try:
            numberofparts = int(request.POST.get('numberofparts') or 0)
        except ValueError:
            numberofparts = 0
        dict_val = {}
        lst = []
        for i in range(numberofparts):
            name_key = 'parts_name-' + str(i)
            value_key = 'parts_image-' + str(i)
            parts_name = request.POST.get(name_key)
            parts_image = request.POST.get(value_key)
            # Skip if fields are missing or empty
            if not parts_name and not parts_image:
                continue
            myli = [parts_name or '', parts_image or '']
            lst.append(myli)
        res_dct = {i[0]: i[1] for i in lst}
        sub = Sub_Category.objects.get(id=s)
        pro1=Product.objects.create(description=desc, bid_type=bid_type, status="pending",session=start, interval_price=end, category=sub, name=p, min_price=pr, final_price=pr, images=im, parameter=res_dct, user=request.user)
        messages.success(request, "Product added successfully.")
        return redirect('view_product')
    d = {'cat': cat,'scat':scat}
    return render(request, 'add_product.html', d)


def edit_product(request, pid):
    if not request.user.is_authenticated:
        return redirect('login_admin')
    
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    data = Product.objects.get(id=pid)
    cat = Category.objects.all()
    scat = Sub_Category.objects.all()
    if request.method=="POST":
        c = request.POST['cat']
        s = request.POST['scat']
        p = request.POST['p_name']
        pr = request.POST['price']
        start = request.POST['start']
        end = request.POST['interval_price']
        desc = request.POST['desc']
        bid_type = request.POST['bid_type']
        try:
            i = request.FILES['image']
            data.images = i
            data.save()
        except:
            pass
        d = request.POST['desc']
        numberofparts = request.POST.get('numberofparts')
        if not numberofparts:
            numberofparts = 0
        edit_len = len(eval(data.parameter))

        lst2 = []
        for i in range(1, int(edit_len)+1):
            parts_name = request.POST['edit_parts_name-'+str(i)]
            parts_image = request.POST['edit_parts_image-'+str(i)]
            myli = [parts_name, parts_image]
            lst2.append(myli)
        dict_val = {i[0]: i[1] for i in lst2}

        lst = []
        for i in range(int(numberofparts)):
            parts_name = request.POST['parts_name-'+str(i)]
            parts_image = request.POST['parts_image-'+str(i)]
            myli = [parts_name, parts_image]
            lst.append(myli)
        res_dct = {i[0]: i[1] for i in lst}
        dict_val.update(res_dct)
        sub = Sub_Category.objects.get(id=s)
        Product.objects.filter(id=pid).update(description=desc, bid_type=bid_type,session=start, interval_price=end, category=sub, name=p, min_price=pr, final_price=pr, parameter=dict_val, user=request.user)
        messages.success(request, "Product Updated")
        return redirect('view_product')
    d = {'cat': cat,'scat':scat, 'data':data}
    return render(request, 'edit_product.html', d)




def load_courses(request):
    if not request.user.is_authenticated:
        return redirect('login')
    programming_id = request.GET.get('programming')
    courses = Sub_Category.objects.filter(category_id=programming_id).order_by('name')
    return render(request, 'courses_dropdown_list_options.html', {'courses': courses})


def view_product(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    product = Product.objects.filter(user=request.user)
    return render(request, 'view_product.html', {'product': product})


def delete_product(request,pid):
    if not request.user.is_authenticated:
        return redirect('login')
    pro = Product.objects.get(id=pid)
    pro.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('view_product')

def product_detail(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    product = Product.objects.get(id=pid)
    return render(request, 'product_detail.html', {'product':product})

def make_participants(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    product = Product.objects.get(id=pid)
    participant = Participants.objects.create(user=request.user, product=product)
    messages.success(request, "Added for participant successfully.")
    return redirect('product_detail', pid)

def getbidhistory(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    product = Product.objects.get(id=pid)
    participant = ParticipantsHistory.objects.filter(product=product).order_by('-id')[:5]
    winner_status = False
    if product.bid_type == "Tendor":
        max_val = product.min_price-product.interval_price
    else:
        max_val = product.min_price+product.interval_price

    if participant.first():
        minutes = datetime.now(timezone.utc) - participant.first().created
        
        if minutes.seconds/60 >= 3 and product.status == "live":
            product.winner = participant.first().user
            product.status = "closed"
            winner_status = True

        
        if product.bid_type == "Tendor":
            max_val = participant.first().new_price-product.interval_price
        else:
            max_val = participant.first().new_price+product.interval_price

    d = {'status':'Success', 'new_price':[], 'name':[], 'time':[], 'maximum':max_val, 'winner_status':winner_status}
    try:
        product.final_price = participant.first().new_price
        product.save()
    except:
        pass
    for i in participant:
        d['new_price'].append(i.new_price)
        d['name'].append(i.user.first_name+" "+i.user.last_name)
        d['time'].append(i.created)
    return JsonResponse(d)

def startbidding(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    
    product = Product.objects.get(id=pid)
    participant1 = ParticipantsHistory.objects.filter(product=product).order_by('-id')[:5]
    new = request.POST.get('new_price')
    
    winner_status = False
    if participant1.first():
        minutes = datetime.now(timezone.utc) - participant1.first().created
        if minutes.seconds/60 >= 3 and product.status == "live":
            product.winner = participant.first().user
            product.status = "closed"
            product.save()
            messages.success(request, "Sorry! You are late, Winner has announced.")
        else:
            participant = ParticipantsHistory.objects.create(user=request.user, product=product, new_price=new)
    else:
        participant = ParticipantsHistory.objects.create(user=request.user, product=product, new_price=new)
    return redirect('product_detail', pid)

def changelivetocomplete(request, pid):
    product = Product.objects.get(id=pid)
    winner = ParticipantsHistory.objects.filter(product=product).last()
    product.status = "closed"
    if winner:
        product.winner = winner.user
    product.save()
    return JsonResponse({'myurl':'/'})

def changeupcomingtolive(request, pid):
    product = Product.objects.get(id=pid)
    winner = ParticipantsHistory.objects.filter(product=product).last()
    product.status = "live"
    product.save()
    return JsonResponse({'myurl':'/'})

def meetwinners(request):
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    product = Product.objects.filter().exclude(winner=None)
    return render(request, 'meetwinners.html', {'product':product})


def all_product(request):
    if request.user.is_authenticated:
        auctionuser = AuctionUser.objects.get(user=request.user)
        if auctionuser.status == "pending":
            messages.success(request, "Your verification is pending. complete your additional detail and email verification. if these are already completed then try login after sometime.We are working on your detail verification.Thanks!")
            return redirect('profile', request.user.id)
    product = Product.objects.filter().exclude(status="pending")
    return render(request, 'HotProducts.html', {'product':product})


def admin_home(request):
    bidder = AuctionUser.objects.filter(user_type="Bidder")
    seller = AuctionUser.objects.filter(user_type="Seller")
    tender = Product.objects.filter(bid_type="Tendor")
    auction = Product.objects.filter(bid_type="Auction")
    d = {'bidder':bidder.count(), 'seller':seller.count(), 'tender':tender.count(), 'auction':auction.count()}
    return render(request, 'administration/admin_home.html', d)


def Admin_Login(request):
    if request.method == "POST":
        u = request.POST['uname']
        p = request.POST['pwd']
        user = authenticate(username=u, password=p)
        try:
            if user.is_staff:
                login(request, user)
                messages.success(request, "Logged in Successfully")
                return redirect('admin_home')
            else:
                messages.success(request, "Invalid Credentials.")
        except:
            messages.success(request, "Invalid Credentials.")
    return render(request,'administration/loginadmin.html')


def view_seller_user(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = AuctionUser.objects.filter(user_type='Seller')
    d = {'user':pro}
    return render(request,'administration/view_seller_user.html',d)


def view_buyer_user(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = AuctionUser.objects.filter(user_type='Bidder')
    d = {'user':pro}
    return render(request,'administration/view_user.html',d)



def view_participants(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = Participants.objects.filter()
    d = {'pro':pro}
    return render(request,'administration/view_participants.html',d)


def Admin_product(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    product = Product.objects.filter()
    d ={'pro':product}
    return render(request,'administration/admin_view_product.html',d)


def Add_Categary(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    error=False
    if request.method=="POST":
        n = request.POST['cat']
        Category.objects.create(name=n)
        messages.success(request, "Added Successfully")
    d = {'error':error}
    return render(request, 'administration/add_category.html', d)


def Add_Sub_Categary(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    error=False
    cat_all = Category.objects.all()
    if request.method=="POST":
        n = request.POST['cat']
        s = request.POST['subcat']
        cat = Category.objects.get(id=n)
        subcat = Sub_Category.objects.create(category=cat, name=s)
        messages.success(request, "Added Successfully")
        return redirect("view_sub_category")
    d = {'error':error, 'cat':cat_all}
    return render(request, 'administration/add_sub_categary.html', d)


def View_Categary(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = Category.objects.all()
    d = {'pro': pro}
    return render(request,'administration/view_category.html', d)


def View_Sub_Categary(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = Sub_Category.objects.all()
    d = {'pro': pro}
    return render(request,'administration/view_sub_category.html', d)


def View_winner(request):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = Product.objects.filter().exclude(winner=None)
    d = {'pro': pro}
    return render(request,'administration/view_winner.html', d)



def delete_admin_product(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    pro = Product.objects.get(id=pid)
    pro.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('admin_view_product')


def delete_category(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = Category.objects.get(id=pid)
    cat.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('view_categary')


def delete_user(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = User.objects.get(id=pid)
    cat.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('view_buyer_user')



def delete_sub_category(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = Sub_Category.objects.get(id=pid)
    cat.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('view_sub_category')


def delete_participant(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = Sub_Category.objects.get(id=pid)
    cat.delete()
    messages.success(request, "Deleted Successfully")
    return redirect('view_participants')


def change_status(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = Product.objects.get(id=pid)
    cat.status = "upcoming"
    cat.save()
    messages.success(request, "Status Changed Successfully")
    return redirect('admin_view_product')


def change_user_status(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    cat = AuctionUser.objects.get(id=pid)
    if cat.status == "Approved":
        cat.status = "pending"
    else:
        cat.status = "Approved"
    cat.save()
    messages.success(request, "Status Changed Successfully")
    if cat.user_type == "Seller":
        return redirect('view_seller_user')
    else:
        return redirect('view_buyer_user')


def Change_Password(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method=="POST":
        n = request.POST['pwd1']
        c = request.POST['pwd2']
        o = request.POST['pwd3']
        if c == n:
            u = User.objects.get(username__exact=request.user.username)
            u.set_password(n)
            u.save()
            messages.success(request, "Changed Successfully")
        else:
            messages.success(request, "Password not matching")
    if request.user.is_staff:
        return render(request, 'administration/change_password.html', )
    else:
        return render(request,'change_password.html')


def profile(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    user = User.objects.get(id=pid)
    pro = AuctionUser.objects.get(user=user)
    d={'pro':pro,'user':user}
    return render(request,'profile.html',d)


def Edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    pro = AuctionUser.objects.get(user=request.user)
    if request.method == 'POST':
        f = request.POST['fname']
        l = request.POST['lname']
        u = request.POST['uname']
        ad = request.POST['add']
        e = request.POST['email']
        con = request.POST['contact']
        d = request.POST['date']
        an = request.POST['adhar_number']
        pn = request.POST['pan_number']
        acn = request.POST['account_number']
        terms = request.POST.get('terms',False)

        try:
            i = request.FILES['img']
            pro.image = i
            pro.save()
        except:
            pass

        try:
            ac = request.FILES['aadhar']
            pro.adhar_card = ac
            pro.save()
        except:
            pass

        try:
            pc = request.FILES['pan']
            pro.pan_card = pc
            pro.save()
        except:
            pass

        try:
            bs = request.FILES['bank_statement']
            pro.bank_statement = bs
            pro.save()
        except:
            pass



        pro.dob = d
        pro.user.username=u
        pro.user.first_name=f
        pro.user.last_name=l
        pro.user.email=e
        pro.contact=con
        pro.address=ad
        pro.adhar_number=an
        pro.account_number=acn
        pro.pan_number=pn
        if terms == "on":
            pro.agree=True
        else:
            pro.agree=False
        pro.save()
        messages.success(request, "updated Successfully")
        return redirect('profile', request.user.id)
    d = {'pro':pro}
    return render(request, 'edit_profile.html',d)

def email_verify(request, pid):
    user = AuctionUser.objects.get(id=pid)
    if request.method == "POST":
        otp = request.POST['otp']
        if user.otp == str(otp):
            user.email_verification = True
            user.save()
            messages.success(request, "Email Varified Successfully")
            return redirect('profile', user.user.id)
        else:
            messages.success(request, "Invalid OTP.")
            return redirect('email_verify', pid)
    return render(request, 'verify_email.html',{'pid':pid})
    

def generateotp(request, pid):
    user = AuctionUser.objects.get(id=pid)
    digits = [i for i in range(0, 10)]
    random_str = ""
    for i in range(6):
        index = math.floor(random.random() * 10)
        random_str += str(digits[index])
    email_host = settings.EMAIL_HOST_USER
    print(user.user.email)
    html_content = "<h4>Your Email Verification code is : </h4><h3>"+str(random_str)+"</h3>"
    email = EmailMessage("Send Verification Code", html_content, str(email_host), [str(user.user.email),])
    email.content_subtype = "html"
    res = email.send()
    user.otp = random_str
    user.save()
    return JsonResponse({'Success':True})

def admin_product_detail(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    product = Product.objects.get(id=pid)
    if request.method == "POST":
        comment = request.POST['comment']
        product.comment = comment
        product.save()
        messages.success(request, "Commented Successfully")
        return redirect('admin_product_detail', pid)
    d = {'product':product, 'booking_id':pid}
    return render(request,'administration/admin_product_detail.html',d)

def bidder_detail(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    data = AuctionUser.objects.get(id=pid)
    d = {'data':data}
    return render(request,'administration/bidder_detail.html',d)

def seller_detail(request,pid):
    if not request.user.is_authenticated:
        return redirect('loginadmin')
    data = AuctionUser.objects.get(id=pid)
    d = {'data':data}
    return render(request,'administration/seller_detail.html',d)
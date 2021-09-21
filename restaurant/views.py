from django.db.models.fields.related import ForeignKey
from django.http.response import HttpResponse
from restaurant.models import Rest, Review
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from member.models import Profile, Member

from selenium import  webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time


#메인페이지
def restaurant(request):
    rest_list_user = Rest.objects.filter(rest_rmd='user').order_by('-id')
    rest_list_kfq = Rest.objects.filter(rest_rmd='kfq')
    rest_list_score = Rest.objects.order_by('-rest_score')
    context = { 'rest_list_user' : rest_list_user, 'rest_list_kfq' : rest_list_kfq , 'rest_list_score' : rest_list_score }
    return render(request, 'restaurant/restaurant.html',context)
    
#게시물 리스트로 보기
def restaurant_list(request): 
    rest_list = Rest.objects.all()
    context = {'rest_list' : rest_list }
    return render(request, 'restaurant/restaurant_list.html', context)

#상세 게시물 보기
def restaurant_detail(request, pk):
    rest = Rest.objects.get(pk=pk)
    review = Review.objects.filter(rest_id = rest)
    writer_nick = dict()
    writer_image = dict()
    for n, user in enumerate(review) :
        member = Member.objects.get(user_name = user.review_writer)
        profile = Profile.objects.get(user_name_id = member.user_phone)
        writer_nick[n] = profile.nickname
        writer_image[n] = profile.image
    
    context = { 'rest' : rest , 'review' : review , 'writer_nick' : writer_nick, 'writer_image' : writer_image}

    return render(request, 'restaurant/restaurant_detail.html', context)

#검색 상세페이지
def restaurant_search(request): 
    search = request.POST.get('search')
    #해당 가게명이 데이터 베이스에 없다.
    if not Rest.objects.filter(rest_name__contains=search).exists() :  
        
        #크롤링
        url = 'https://www.mangoplate.com/'
        #webdriver.DesiredCapabilities.CHROME['acceptSslCerts']=True
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        options.add_argument('--no-sandbox')
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")

        driver =  webdriver.Chrome(chrome_options=options) #executable_path='static/chromedriver.exe', 
        driver.get(url)
        time.sleep(0.5)
        elem = driver.find_element_by_class_name('Header__LogoIcon')
        action_chains = ActionChains(driver)
        action_chains.move_to_element_with_offset(elem, 0, 0).perform()
        action_chains.click().perform()

        element=driver.find_element_by_name('main-search') #검색란 찾기
        element.send_keys(search) #검색어 입력

        ser_btn=driver.find_element_by_class_name("btn-search")# 검색찾기
        ser_btn.click()

        #검색어가 존재하지 않을 시
        try :
            elem2 = driver.find_element_by_class_name('thumb')
        except :
            rest_list_user = Rest.objects.filter(rest_rmd='user').order_by('-id')
            rest_list_kfq = Rest.objects.filter(rest_rmd='kfq')
            rest_list_score = Rest.objects.order_by('-rest_score')
            er = f"{search} 검색어가 존재하지 않습니다."
            context = {'er':er,'search':search, 'rest_list_user' : rest_list_user, 'rest_list_kfq' : rest_list_kfq , 'rest_list_score' : rest_list_score}
            return render(request, 'restaurant/restaurant.html',context)
        
        action_chains = ActionChains(driver)
        action_chains.move_to_element_with_offset(elem2, 0, 0).perform()
        action_chains.click().perform()
        html = driver.page_source
        rest_url = driver.current_url.split('/')[-1]

        #만약 같은 url 주소를 가진 것이 없다면 데이터를 수집한다.
        if not Rest.objects.filter(rest_url = rest_url).exists() : 
            soup = BeautifulSoup(html, 'html.parser')

            # 이미지 크롤링
            img_list = soup.select('.restaurant-photos-item img')
            img_list #이미지 주소
            img_url_list = [] #이미지 주소 리스트
            for img in img_list: 
                rest_photo_url = img.attrs['src']
                img_url_list.append(rest_photo_url)

            if len(img_url_list) > 0 : 
                rest_img1 = img_url_list[0] #대표이미지 저장
            if len(img_url_list) > 1 :
                rest_img2 = str()
                for i in img_url_list[1:] :
                    rest_img2 += i + '@@' #이미지 갯수만큼 저장 후 '@@'를 통해서 분리
                rest_img2 = rest_img2[:-2]
            # 가게명 크롤링
            name = soup.select('.restaurant_name')
            rest_name = name[0].text
            # 점수 크롤링
            try :
                score = soup.select('.rate-point')
                rest_score = score[0].text #점수
            except :
                rest_score = 0
            # 주소 크롤링
            td = soup.select('section.restaurant-detail > ul > li:nth-child(1) > div.Restaurant__InfoItemLabel > div.Restaurant__InfoItemLabel--RoadAddressText')
            rest_address = td[0].text
            # 가게 전화번호 크롤링
            tel = soup.select('section.restaurant-detail > table > tbody > tr:nth-child(2) > td')
            rest_tel = tel[0].text
            # 가게 음식종류 크롤링
            td = soup.select('body > main > article > div.column-wrapper > div.column-contents > div > section.restaurant-detail > table > tbody > tr:nth-child(3) > td')
            if len(td) > 0:
                rest_kind = td[0].text
            # 가격대 크롤링
            td = soup.select('body > main > article > div.column-wrapper > div.column-contents > div > section.restaurant-detail > table > tbody > tr:nth-child(4) > td')
            if len(td) > 0:
                rest_price = td[0].text

            rest = Rest(
                rest_update = timezone.now(),
                rest_tel = rest_tel,
                rest_name = rest_name,
                rest_address = rest_address,
                rest_kind = rest_kind,
                rest_score = rest_score,
                rest_url = rest_url,
            )
            # 존재한다면 저장
            if 'rest_price' in locals():
                rest_price = rest_price
            if 'rest_img1' in locals() :
                rest.rest_img1 = rest_img1
            if 'rest_img2' in locals() :
                rest.rest_img2 = rest_img2
            rest.save()
        else :
            rest = Rest.objects.get(rest_url = rest_url)
    else :
        #검색어가 포함된 가게명 불러오기
        rest = Rest.objects.get(rest_name__contains=search)

    return redirect('/restaurant/'+ str(rest.id))
    
#게시글 review
def restaurant_review(request, pk):
    
    rest = get_object_or_404(Rest, pk = pk)
    score = request.POST.get('score')
    review_score = float(score)
    review_writer = request.session['user_name']
    review_content = request.POST.get('comment')
    review_date = timezone.now()
    rest_id = rest
    
    Re = Review(rest_id = rest_id,
                review_score = review_score,
                review_writer = review_writer,
                review_content = review_content,
                review_date = review_date)
    Re.save()
    return redirect('/restaurant/'+ str(rest.id))
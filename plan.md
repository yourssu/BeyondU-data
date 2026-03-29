# university 테이블 데이터 스키마 변경
1. created_at, updated_at 추가하기. 
- 각각 데이터 생성/수정 날짜를 의미
2. remark에서 location(string), studentNumber(string) 분리해서 저장한다. 
- 보통 "위치: Groningen, Assen, Leeuwarden * 특징: 학생 수 약 28,000명 #151-200 THE European Teaching Rankings 2018" 이렇게 저장이 되어있는데
- 위치: 오른쪽에 있는 데이터인 'Groningen, Assen, Leeuwarden' 이 부분을 location에 저장하고 
- 특징: 오른쪽에 있는 '학생 수 약 28,000명'에서 28000을 studentNumber로 저장
- remark 데이터는 일단 지우지 않고 남겨놓는다.
3. available_majors → available_major(string)수강가능학과 / available_subject(string)수강가능과목 분리
- available_majors에 있는 데이터를 보면 ★ 수학가능학과: Life Science & Technology, Engineering, Future Environments, International Business School, Minerva Art Academy, Prince Claus Conservatoire, Business, Marketing and Finance, Buiness Management, Communication, Media & IT, Education, Health Care Studies, Law, Social Studies, Sports Studies ★ 수강가능과목(2024): https://www.hanze.nl/en/study/studying-at-hanze/exchange-programmes "Programme Overview" 부분 각 전공 클릭하면 확인 가능 → course catalogue 확인 URL: https://catalogue.hanze.nl/en?_gl=1*1p629ax*_gcl_au*MzI3MTg0MzAyLjE3Mzc1NTAxNjc. 이렇게 되어있어
- 이 칼럼을 available_major(string), available_subject(string) 이렇게 쪼갤 거야
- available_major(string)는 '★ 수학가능학과: Life Science & Technology, Engineering, Future Environments, International Business School, Minerva Art Academy, Prince Claus Conservatoire, Business, Marketing and Finance, Buiness Management, Communication, Media & IT, Education, Health Care Studies, Law, Social Studies, Sports Studies' 에서 'Life Science & Technology, Engineering, Future Environments, International Business School, Minerva Art Academy, Prince Claus Conservatoire, Business, Marketing and Finance, Buiness Management, Communication, Media & IT, Education, Health Care Studies, Law, Social Studies, Sports Studies' 이 부분만 파싱 되도록 로직 구현 후에 저장
- available_subject(string)는 '★ 수강가능과목(2024): https://www.hanze.nl/en/study/studying-at-hanze/exchange-programmes "Programme Overview" 부분 각 전공 클릭하면 확인 가능 → course catalogue 확인 URL: https://catalogue.hanze.nl/en?_gl=1*1p629ax*_gcl_au*MzI3MTg0MzAyLjE3Mzc1NTAxNjc. 이렇게 되어있어' 에서 'https://www.hanze.nl/en/study/studying-at-hanze/exchange-programmes' 이 url 부분을 파싱하고 저장하기

# language_requirement 테이블 데이터 스키마 변경
1. is_availalbe false인 어학요구사항 제거
- is_availalbe이 false인 데이터는 의미가 아예 없는 데이터임
- is_availalbe가 true인 것만 데이터를 만듦
- 기존의 로직에서는 '~ 제외'라고 나와있으면 해당되는 어학 성적의 is_availalbe를 false로 만들고 있음
- 이를 false로 만들고 0인 데이터 싹 다 delete 해서 이 칼럼를 제외하도록 로직 수정


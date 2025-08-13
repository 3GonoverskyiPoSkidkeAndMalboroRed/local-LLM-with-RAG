`Быстрый сетап переменных окружения (Git Bash)`
BASE_URL="http://localhost:8000"

# Подставьте ваши токены
TOKEN_ADMIN="eyJ..."   # JWT админа
TOKEN_USER="eyJ..."    # JWT обычного пользователя

# Примеры идентификаторов
USER_ID=1              # текущий пользователь
OTHER_USER_ID=2        # другой пользователь
CONTENT_ID=10
DEPARTMENT_ID=1
ACCESS_LEVEL=1
TAG_ID=5
FILENAME="example.txt"


`Как получить токен (опционально)`
# Админ
TOKEN_ADMIN=$(curl -s -X POST "$BASE_URL/user/login" -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"adminpass"}' | jq -r .access_token)

# Обычный пользователь
TOKEN_USER=$(curl -s -X POST "$BASE_URL/user/login" -H "Content-Type: application/json" \
  -d '{"login":"alex","password":"alexpass"}' | jq -r .access_token)


`user_routes`
# GET /user/{id}  (в коде: /user/user/{id}) — токен обязателен, доступ себе или админу
curl -H "Authorization: Bearer $TOKEN_USER" "$BASE_URL/user/user/$USER_ID"

# GET /user/{user_id}/content  (в коде: /user/user/{user_id}/content) — токен, себе или админу
curl -H "Authorization: Bearer $TOKEN_USER" "$BASE_URL/user/user/$USER_ID/content"

# GET /users  (в коде: /user/users) — только админ
curl -H "Authorization: Bearer $TOKEN_ADMIN" "$BASE_URL/user/users"

# PUT /user/{user_id}  (в коде: /user/user/{user_id}) — только админ
curl -X PUT -H "Authorization: Bearer $TOKEN_ADMIN" -H "Content-Type: application/json" \
  -d '{"department_id": 1, "access_id": 1}' \
  "$BASE_URL/user/user/$OTHER_USER_ID"

# DELETE /user/{user_id}  (в коде: /user/user/{user_id}) — только админ
curl -X DELETE -H "Authorization: Bearer $TOKEN_ADMIN" \
  "$BASE_URL/user/user/$OTHER_USER_ID"

# PUT /user/{user_id}/password  (в коде: /user/user/{user_id}/password) — владелец или админ
curl -X PUT -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" \
  -d '{"password":"newStrongPass"}' \
  "$BASE_URL/user/user/$USER_ID/password"


`content_routes`
# GET /content/all — только админ
curl -H "Authorization: Bearer $TOKEN_ADMIN" "$BASE_URL/content/all"

# GET /content/filter  (в коде: /content/content/filter) — токен + соответствие access/department либо админ
curl -G -H "Authorization: Bearer $TOKEN_USER" \
  --data-urlencode "access_level=$ACCESS_LEVEL" \
  --data-urlencode "department_id=$DEPARTMENT_ID" \
  "$BASE_URL/content/content/filter"

# GET /content/{content_id}  (в коде: /content/content/{content_id}) — токен + проверка доступа
curl -H "Authorization: Bearer $TOKEN_USER" "$BASE_URL/content/content/$CONTENT_ID"

# PUT /{content_id}  (в коде: /content/{content_id}) — только админ
curl -X PUT -H "Authorization: Bearer $TOKEN_ADMIN" -H "Content-Type: application/json" \
  -d '{"title":"New title","description":"Updated"}' \
  "$BASE_URL/content/$CONTENT_ID"

# GET /user/{user_id}/content/by-tags/{tag_id}  (в коде: /content/user/{user_id}/content/by-tags/{tag_id}) — токен, себе или админ
curl -H "Authorization: Bearer $TOKEN_USER" \
  "$BASE_URL/content/user/$USER_ID/content/by-tags/$TAG_ID"

# GET /search-documents  (в коде: /content/search-documents?user_id=...&search_query=...) — токен, себе или админ
curl -G -H "Authorization: Bearer $TOKEN_USER" \
  --data-urlencode "user_id=$USER_ID" \
  --data-urlencode "search_query=Doc" \
  "$BASE_URL/content/search-documents"

# Админ-операции с файлами каталога
# GET /list-files/{department_id}
curl -H "Authorization: Bearer $TOKEN_ADMIN" "$BASE_URL/content/list-files/$DEPARTMENT_ID"

# DELETE /delete-file/{department_id}/{filename}
curl -X DELETE -H "Authorization: Bearer $TOKEN_ADMIN" \
  "$BASE_URL/content/delete-file/$DEPARTMENT_ID/$FILENAME"

# DELETE /delete-all-files/{department_id}
curl -X DELETE -H "Authorization: Bearer $TOKEN_ADMIN" \
  "$BASE_URL/content/delete-all-files/$DEPARTMENT_ID"

# GET /list-all-departments
curl -H "Authorization: Bearer $TOKEN_ADMIN" "$BASE_URL/content/list-all-departments"


`feedback_routes`
# POST /create — токен, только от своего имени (или админ за кого-то)
curl -X POST -H "Authorization: Bearer $TOKEN_USER" \
  -F "user_id=$USER_ID" -F "text=Hello" \
  "$BASE_URL/feedback/create"

# (с фото)
curl -X POST -H "Authorization: Bearer $TOKEN_USER" \
  -F "user_id=$USER_ID" -F "text=Hello" -F "photo=@/path/to/image.jpg" \
  "$BASE_URL/feedback/create"

# GET /list — только админ
curl -H "Authorization: Bearer $TOKEN_ADMIN" "$BASE_URL/feedback/list"

# GET /photo/{feedback_id} — токен, автор или админ
curl -H "Authorization: Bearer $TOKEN_USER" "$BASE_URL/feedback/photo/123"

# GET /detail/{feedback_id} — токен, автор или админ
curl -H "Authorization: Bearer $TOKEN_USER" "$BASE_URL/feedback/detail/123"
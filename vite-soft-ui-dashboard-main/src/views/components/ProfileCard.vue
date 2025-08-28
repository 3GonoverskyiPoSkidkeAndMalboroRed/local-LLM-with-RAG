<template>
  <div class="card h-100">
    <div class="p-3 pb-0 card-header">
      <div class="row">
        <div class="col-md-8 d-flex align-items-center">
          <h6 class="mb-0">Подробная информация о пользователе</h6>
        </div>
      </div>
    </div>
    <div class="p-3 card-body">
      <hr class="my-1 horizontal gray-light" />
      <ul class="list-group">
        <li class="pt-0 text-sm border-0 list-group-item ps-0">
          <strong class="text-dark">Логин:</strong> &nbsp; {{ user.login }}
        </li>
        <li class="text-sm border-0 list-group-item ps-0">
          <strong class="text-dark">ФИО:</strong> &nbsp; {{ user.full_name }}
        </li>
        <li class="text-sm border-0 list-group-item ps-0">
          <strong class="text-dark">Роль:</strong> &nbsp; {{ user.role_name }}
        </li>
        <li class="text-sm border-0 list-group-item ps-0">
          <strong class="text-dark">Отдел:</strong> &nbsp; {{ user.department_name }}
        </li>
        <li class="text-sm border-0 list-group-item ps-0">
          <strong class="text-dark">Уровень доступа:</strong> &nbsp; {{ user.access_name }}
        </li>
        <li class="pb-0 border-0 list-group-item ps-0">
          <strong class="text-sm text-dark">ID пользователя:</strong> &nbsp; {{ user.id }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: "ProfileCard",
  props: {
    user: {
      type: Object,
      required: true
    }
  }
};
</script>

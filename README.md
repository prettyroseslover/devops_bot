# Ansible Branch

> :warning: **Ubuntu**: Установка зависимостей через playbook реализована именно для apt-дистрибутивов!

Управление playbook'ом происходит с помощью файла `secrets.yaml` следующего содержания:

```yaml
invent: # Настройки для inventory
  bot:  # Использую подготовленного пользователя ansible
    host: <ip-адрес>
    user: ansible
    password: <Пароль>
  db:
    host: <ip-адрес>
    user: ansible
    password: <Пароль>
  db_repl:
    host: <ip-адрес>
    user: ansible
    password: <Пароль>

telegram: # Для бота
  token: <Токен для бота>
databases: 
  master: # Для БД
    user: <Пользовтель db>
    password: <Пароль>
    database: <Название базы данных>
    port: <Номер порта>
  replica: # Для реплики
    user: <Пользователь db_repl>
    password: <Пароль>
    port: <Номер порта>
remote_monitoring: # Для удаленной машины, которую мониторит бот
  host: <ip-адрес>
  user: <Пользователь удаленной машины для подключения по SSH>
  password: <Пароль>
  port: <Номер порта SSH>

```

Для запуска playbook'а необходимо иметь установленный Ansible (установка Ansible вне скоупа этого README). Запуск playbook'а осуществляется следующим образом:

```bash
ansible-playbook playbook_tg_bot.yml -i inventory -e @secrets.yaml
```

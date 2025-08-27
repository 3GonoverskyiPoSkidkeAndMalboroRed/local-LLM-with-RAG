-- MySQL dump 10.13  Distrib 9.3.0, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: db_main
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `access`
--

DROP TABLE IF EXISTS `access`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `access` (
  `id` int NOT NULL AUTO_INCREMENT,
  `access_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Для указания уровня доступа';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access`
--

LOCK TABLES `access` WRITE;
/*!40000 ALTER TABLE `access` DISABLE KEYS */;
INSERT INTO `access` VALUES (1,'Базовый'),(2,'Повышенный'),(3,'Админ'),(4,'Публичный'),(5,'Внутренний'),(6,'Конфиденциальный'),(7,'Секретный');
/*!40000 ALTER TABLE `access` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content`
--

DROP TABLE IF EXISTS `content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text,
  `file_path` varchar(255) NOT NULL,
  `access_level` int NOT NULL,
  `department_id` int NOT NULL,
  `tag_id` int DEFAULT NULL,
  `creator_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` enum('active','inactive','archived') DEFAULT 'active',
  PRIMARY KEY (`id`),
  KEY `fk_content_access` (`access_level`),
  KEY `fk_content_department` (`department_id`),
  KEY `fk_content_tag` (`tag_id`),
  KEY `fk_content_creator_idx` (`creator_id`),
  CONSTRAINT `fk_content_access` FOREIGN KEY (`access_level`) REFERENCES `access` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_content_creator` FOREIGN KEY (`creator_id`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_content_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_content_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Таблица для хранения контента';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content`
--

LOCK TABLES `content` WRITE;
/*!40000 ALTER TABLE `content` DISABLE KEYS */;
INSERT INTO `content` VALUES (36,'Инструкция','Инструкция по выдаче ТМЦ от производства','/app/files/Инструкция по выдаче ТМЦ от производства.pdf',2,4,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(37,'Инструкция','Инструкция по выпуску готовой продукции','/app/files/Инструкция по выпуску готовой продукции.pdf',2,4,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(38,'Инструкция','Инструкция по заполнению справочника номенклатуры по ответственным','/app/files/Инструкция по заполнению справочника номенклатуры по ответственным.pdf',2,4,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(39,'GF2E','Качественный анализ_2017','/app/files/Руководство - Качественный анализ_2017.pdf',2,4,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(40,'Руководство GF2E','Количественный анализ_GF-2E','/app/files/Руководство - Количественный анализ_GF-2E.pdf',2,4,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(41,'Видео GF2E','1.Анализ G(GF)','/app/files/1.Анализ G(GF).mp4',2,4,4,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(42,'Видео GF2E','2.Переградуировка G(GF)','/app/files/2.Переградуировка G(GF).mp4',2,4,4,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(43,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/Research/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(44,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/Research/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(45,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/Research/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(46,'Для рэг','12','/app/files/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',3,5,5,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(47,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/ContentDep\\5/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(48,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/ContentDep/5/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(49,'[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf','Загруженный файл','/app/files/ContentDep/4/[2]_Черноруков-Теория и практика рентгенофлуоресцентного анализа.pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(50,'[3]_2008-Лекции-Рентгеноспектральный флуоресцентный анализ-Казанский Гос. Универ..pdf','Загруженный файл','/app/files/ContentDep/4/[3]_2008-Лекции-Рентгеноспектральный флуоресцентный анализ-Казанский Гос. Универ..pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(51,'1С для ОНТР (2) (1).pdf','Загруженный файл','/app/files/ContentDep/4/1С для ОНТР (2) (1).pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(52,'1С для ОНТР (2) (1).pdf','Загруженный файл','/app/files/Research/1С для ОНТР (2) (1).pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(53,'Список телефонов 2025 (2).pdf','Загруженный файл','/app/files/Research/Список телефонов 2025 (2).pdf',1,1,NULL,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(54,'123','123','/app/files/ContentForDepartment/AllTypesOfFiles/5/SE_TC_Сценарии_работы_SSP2.5_v2.pdf',3,5,2,NULL,'2025-08-27 09:23:26','2025-08-27 09:23:26','active'),(55,'Руководство по использованию системы','Подробное руководство по работе с системой управления документами','test_document.txt',2,5,1,NULL,'2025-08-27 09:43:35',NULL,'active'),(56,'Тестовый документ от ответственного','Описание тестового документа от ответственного','',1,1,1,NULL,'2025-08-27 09:44:50',NULL,'active'),(57,'Тестовый документ от ответственного','Описание тестового документа от ответственного','/app/files/ContentForDepartment/1/proposal_41_test_document_ответственного.txt',1,1,NULL,NULL,'2025-08-27 09:53:51',NULL,'active'),(58,'123','123','/app/files/ContentForDepartment/9/proposal_48_SE_TC_Выпуск_Изменение_КД.pdf',2,9,1,48,'2025-08-27 10:34:37',NULL,'active'),(59,'123','123','/app/files/ContentForDepartment/5/proposal_47_SE_TC_Сценарии_работы_SSP2.5_v2.pdf',2,5,1,47,'2025-08-27 10:40:57',NULL,'active');
/*!40000 ALTER TABLE `content` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `content_proposals`
--

DROP TABLE IF EXISTS `content_proposals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `content_proposals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text,
  `access_level` int NOT NULL,
  `department_id` int NOT NULL,
  `tag_id` int DEFAULT NULL,
  `proposed_by` int NOT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `reviewed_by` int DEFAULT NULL,
  `review_comment` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `file_path` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_proposal_department_idx` (`department_id`),
  KEY `fk_proposal_access_idx` (`access_level`),
  KEY `fk_proposal_tag_idx` (`tag_id`),
  KEY `fk_proposal_user_idx` (`proposed_by`),
  KEY `fk_proposal_reviewer_idx` (`reviewed_by`),
  CONSTRAINT `fk_proposal_access` FOREIGN KEY (`access_level`) REFERENCES `access` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_proposal_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_proposal_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_proposal_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_proposal_user` FOREIGN KEY (`proposed_by`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `content_proposals`
--

LOCK TABLES `content_proposals` WRITE;
/*!40000 ALTER TABLE `content_proposals` DISABLE KEYS */;
INSERT INTO `content_proposals` VALUES (12,'123','123',2,9,1,48,'approved',47,'Предложение одобрено','2025-08-27 10:33:36','2025-08-27 10:34:37','/app/files/proposals/proposal_48_SE_TC_Выпуск_Изменение_КД.pdf'),(13,'123','123',2,5,1,47,'approved',47,'Предложение одобрено','2025-08-27 10:40:28','2025-08-27 10:40:57','/app/files/proposals/proposal_47_SE_TC_Сценарии_работы_SSP2.5_v2.pdf');
/*!40000 ALTER TABLE `content_proposals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department`
--

DROP TABLE IF EXISTS `department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Для указания отдела';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department`
--

LOCK TABLES `department` WRITE;
/*!40000 ALTER TABLE `department` DISABLE KEYS */;
INSERT INTO `department` VALUES (1,'Клиенты'),(2,'Сервисная служба'),(3,'Отдел продаж'),(4,'Отдел методик'),(5,'Админ'),(6,'IT отдел'),(7,'HR отдел'),(8,'Финансовый отдел'),(9,'Маркетинг'),(10,'Общий отдел');
/*!40000 ALTER TABLE `department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `document_chunks`
--

DROP TABLE IF EXISTS `document_chunks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `document_chunks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `content_id` int NOT NULL,
  `department_id` int NOT NULL,
  `chunk_text` text NOT NULL,
  `chunk_index` int NOT NULL,
  `embedding_vector` json DEFAULT NULL,
  `images` json DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_content_id` (`content_id`),
  KEY `idx_department_id` (`department_id`),
  CONSTRAINT `document_chunks_ibfk_1` FOREIGN KEY (`content_id`) REFERENCES `content` (`id`) ON DELETE CASCADE,
  CONSTRAINT `document_chunks_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `document_chunks`
--

LOCK TABLES `document_chunks` WRITE;
/*!40000 ALTER TABLE `document_chunks` DISABLE KEYS */;
/*!40000 ALTER TABLE `document_chunks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedback`
--

DROP TABLE IF EXISTS `feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedback` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `text` varchar(255) NOT NULL,
  `photo` blob,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ix_feedback_id` (`id`),
  CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedback`
--

LOCK TABLES `feedback` WRITE;
/*!40000 ALTER TABLE `feedback` DISABLE KEYS */;
/*!40000 ALTER TABLE `feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions`
--

DROP TABLE IF EXISTS `questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int NOT NULL,
  `text` text NOT NULL,
  `question_type` varchar(20) NOT NULL,
  `options` json DEFAULT NULL,
  `correct_answer` json DEFAULT NULL,
  `order` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `quiz_id` (`quiz_id`),
  KEY `ix_questions_id` (`id`),
  CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions`
--

LOCK TABLES `questions` WRITE;
/*!40000 ALTER TABLE `questions` DISABLE KEYS */;
INSERT INTO `questions` VALUES (1,2,'Какой язык программирования вы предпочитаете?','single_choice','[{\"id\": 1, \"text\": \"Python\"}, {\"id\": 2, \"text\": \"Java\"}, {\"id\": 3, \"text\": \"JavaScript\"}, {\"id\": 4, \"text\": \"C++\"}]','\"1\"',1),(2,2,'Какой фреймворк вы используете чаще всего?','single_choice','[{\"id\": 1, \"text\": \"Django\"}, {\"id\": 2, \"text\": \"Flask\"}, {\"id\": 3, \"text\": \"Spring\"}, {\"id\": 4, \"text\": \"React\"}]','\"1\"',2),(3,2,'Какой тип разработки вам больше нравится?','multiple_choice','[{\"id\": 1, \"text\": \"Веб-разработка\"}, {\"id\": 2, \"text\": \"Мобильная разработка\"}, {\"id\": 3, \"text\": \"Разработка игр\"}, {\"id\": 4, \"text\": \"Научные вычисления\"}]','[\"1\", \"2\"]',3),(4,2,'Какой инструмент для контроля версий вы используете?','single_choice','[{\"id\": 1, \"text\": \"Git\"}, {\"id\": 2, \"text\": \"SVN\"}, {\"id\": 3, \"text\": \"Mercurial\"}, {\"id\": 4, \"text\": \"Не использую\"}]','\"1\"',4),(5,2,'Как часто вы изучаете новые технологии?','single_choice','[{\"id\": 1, \"text\": \"Каждый день\"}, {\"id\": 2, \"text\": \"Несколько раз в неделю\"}, {\"id\": 3, \"text\": \"Несколько раз в месяц\"}, {\"id\": 4, \"text\": \"Редко\"}]','\"1\"',5),(6,2,'Какой метод разработки вы предпочитаете?','single_choice','[{\"id\": 1, \"text\": \"Agile\"}, {\"id\": 2, \"text\": \"Waterfall\"}, {\"id\": 3, \"text\": \"Scrum\"}, {\"id\": 4, \"text\": \"Kanban\"}]','\"1\"',6),(7,2,'Какой тип базы данных вы предпочитаете?','single_choice','[{\"id\": 1, \"text\": \"SQL\"}, {\"id\": 2, \"text\": \"NoSQL\"}, {\"id\": 3, \"text\": \"In-memory\"}, {\"id\": 4, \"text\": \"Не использую базы данных\"}]','\"1\"',7),(8,2,'Какой подход к тестированию вы используете?','multiple_choice','[{\"id\": 1, \"text\": \"Юнит-тестирование\"}, {\"id\": 2, \"text\": \"Интеграционное тестирование\"}, {\"id\": 3, \"text\": \"Системное тестирование\"}, {\"id\": 4, \"text\": \"Не тестирую\"}]','[\"1\", \"2\"]',8),(9,2,'Какой инструмент для управления проектами вы используете?','single_choice','[{\"id\": 1, \"text\": \"Jira\"}, {\"id\": 2, \"text\": \"Trello\"}, {\"id\": 3, \"text\": \"Asana\"}, {\"id\": 4, \"text\": \"Не использую\"}]','\"1\"',9),(10,2,'Какой тип обучения вы предпочитаете?','single_choice','[{\"id\": 1, \"text\": \"Онлайн-курсы\"}, {\"id\": 2, \"text\": \"Книги\"}, {\"id\": 3, \"text\": \"Вебинары\"}, {\"id\": 4, \"text\": \"Личное обучение\"}]','\"1\"',10),(11,3,'укеукеукеу','single_choice','[{\"id\": 1, \"text\": \"куеукеуукку\"}, {\"id\": 2, \"text\": \"укеукеуке\"}]','\"\"',1),(12,3,'укеукееуеук','single_choice','[{\"id\": 1, \"text\": \"укеукеук\"}, {\"id\": 2, \"text\": \"укеуке\"}]','\"\"',2),(13,3,'укеукеуке','single_choice','[{\"id\": 1, \"text\": \"уеукеу\"}, {\"id\": 2, \"text\": \"укеук\"}]','\"\"',3),(14,4,'цукцкцукцу','single_choice','[{\"id\": 1, \"text\": \"цукцукцук\"}, {\"id\": 2, \"text\": \"цукцукцукцук\"}, {\"id\": 3, \"text\": \"цукцукцук\"}]','\"1\"',1),(15,4,'ваипрывтрцурук','single_choice','[{\"id\": 1, \"text\": \"ывапывапыва\"}, {\"id\": 2, \"text\": \"ывапывап\"}, {\"id\": 3, \"text\": \"ывапывпыва\"}]','\"2\"',2),(16,5,'1','single_choice','[{\"id\": 1, \"text\": \"ываыва\"}, {\"id\": 2, \"text\": \"ываыва\"}]','\"\"',1),(17,5,'ываыва','single_choice','[{\"id\": 1, \"text\": \"ываываы\"}, {\"id\": 2, \"text\": \"ваываыва\"}]','\"\"',2),(18,6,'ываыва','single_choice','[{\"id\": 1, \"text\": \"ываыва\"}, {\"id\": 2, \"text\": \"ываыв\"}]','\"1\"',1),(19,6,'аываыв','single_choice','[{\"id\": 1, \"text\": \"ваыва\"}, {\"id\": 2, \"text\": \"ыв\"}]','\"2\"',2),(20,6,'ываываыва','multiple_choice','[{\"id\": 1, \"text\": \"ываыва\"}, {\"id\": 2, \"text\": \"ываыва\"}, {\"id\": 3, \"text\": \"ывавыа\"}]','[\"1\", \"2\"]',3),(21,7,'2+2','single_choice','[{\"id\": 1, \"text\": \"1\"}, {\"id\": 2, \"text\": \"2\"}, {\"id\": 3, \"text\": \"3\"}, {\"id\": 4, \"text\": \"4\"}]','\"4\"',4),(22,7,'3+3','single_choice','[{\"id\": 1, \"text\": \"1\"}, {\"id\": 2, \"text\": \"2\"}, {\"id\": 3, \"text\": \"5\"}, {\"id\": 4, \"text\": \"6\"}]','\"4\"',4),(23,8,'3+3','single_choice','[{\"id\": 1, \"text\": \"6\"}]','\"1\"',1),(24,8,'2+2','single_choice','[{\"id\": 1, \"text\": \"4\"}]','\"1\"',2),(25,9,'укцукцукцу','single_choice','[{\"id\": 1750245309635, \"text\": \"1\"}]','1750245309635',1),(26,9,'выаываываыв','single_choice','[{\"id\": 1750245317989, \"text\": \"1\"}]','1750245317989',2),(27,10,'2+2','single_choice','[{\"id\": 1752230006121, \"text\": \"три\"}, {\"id\": 1752230006122, \"text\": \"2\"}, {\"id\": 1752230006123, \"text\": \"4\"}]','1752230006123',1),(28,10,'3+3','multiple_choice','[{\"id\": 1752230028812, \"text\": \"6\"}, {\"id\": 1752230028813, \"text\": \"Шесть\"}, {\"id\": 1752230028814, \"text\": \"2\"}]','[1752230028812, 1752230028813]',2),(29,11,'Сколько по вашему мнению будет 2+2','single_choice','[{\"id\": 1752230088978, \"text\": \"Четыре\"}, {\"id\": 1752230088979, \"text\": \"2\"}, {\"id\": 1752230088980, \"text\": \"4\"}]','\"\"',1),(30,11,'Сколько по вашему мнению будет 6+6','multiple_choice','[{\"id\": 1752230114771, \"text\": \"Ничего\"}, {\"id\": 1752230114772, \"text\": \"6\"}, {\"id\": 1752230114773, \"text\": \"Шесть\"}]','[]',2);
/*!40000 ALTER TABLE `questions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `quizzes`
--

DROP TABLE IF EXISTS `quizzes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quizzes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text,
  `is_test` tinyint(1) DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  `access_level` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  KEY `access_level` (`access_level`),
  KEY `ix_quizzes_id` (`id`),
  CONSTRAINT `quizzes_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`),
  CONSTRAINT `quizzes_ibfk_2` FOREIGN KEY (`access_level`) REFERENCES `access` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `quizzes`
--

LOCK TABLES `quizzes` WRITE;
/*!40000 ALTER TABLE `quizzes` DISABLE KEYS */;
INSERT INTO `quizzes` VALUES (2,'Опрос о предпочтениях в программировании','Этот опрос поможет нам понять ваши предпочтения в области программирования.',0,4,2,'2025-06-18 09:01:45'),(3,'кеукеукук','укеукеукуе',0,5,3,'2025-06-18 10:45:13'),(4,'цукцукцукцу','кцукцк',1,5,3,'2025-06-18 10:45:59'),(5,'ваыаываываыва','аываываыв',0,5,3,'2025-06-18 10:55:42'),(6,'ываыва','ыва',1,5,3,'2025-06-18 10:56:12'),(7,'сложение','аываывав',1,5,3,'2025-06-18 11:05:40'),(8,'213213213','ЫААФЫВА',1,5,3,'2025-06-18 11:07:15'),(9,'цукцукцу','цукцукцукцу',1,5,3,'2025-06-18 11:15:27'),(10,'Пробное тестирование 1','Пробное тестирование 1',1,4,2,'2025-07-11 10:34:33'),(11,'Пробная анкета 1','Пробная анкета 1',0,4,2,'2025-07-11 10:35:39');
/*!40000 ALTER TABLE `quizzes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rag_sessions`
--

DROP TABLE IF EXISTS `rag_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rag_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_id` int NOT NULL,
  `is_initialized` tinyint(1) DEFAULT '0',
  `documents_count` int DEFAULT '0',
  `chunks_count` int DEFAULT '0',
  `last_updated` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_department` (`department_id`),
  CONSTRAINT `rag_sessions_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rag_sessions`
--

LOCK TABLES `rag_sessions` WRITE;
/*!40000 ALTER TABLE `rag_sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `rag_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role`
--

DROP TABLE IF EXISTS `role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role` (
  `id` int NOT NULL AUTO_INCREMENT,
  `role_name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role`
--

LOCK TABLES `role` WRITE;
/*!40000 ALTER TABLE `role` DISABLE KEYS */;
INSERT INTO `role` VALUES (1,'Админ'),(2,'Пользователь'),(3,'Глава отдела'),(4,'Ответственный отдела');
/*!40000 ALTER TABLE `role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tags`
--

LOCK TABLES `tags` WRITE;
/*!40000 ALTER TABLE `tags` DISABLE KEYS */;
INSERT INTO `tags` VALUES (1,'Административная документация'),(2,'Обучение'),(4,'Поддержка'),(5,'Маркетинговые материалы'),(8,'Документация'),(9,'Политики'),(10,'Процедуры');
/*!40000 ALTER TABLE `tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `login` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role_id` int NOT NULL,
  `department_id` int NOT NULL,
  `access_id` int NOT NULL,
  `auth_key` varchar(255) DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `login_UNIQUE` (`login`),
  KEY `role_id_idx` (`role_id`),
  KEY `fk_user_department_idx` (`department_id`),
  KEY `fk_user_access_idx` (`access_id`),
  CONSTRAINT `fk_user_access` FOREIGN KEY (`access_id`) REFERENCES `access` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_department` FOREIGN KEY (`department_id`) REFERENCES `department` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_user_role` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Таблица для пользователя';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (47,'Pavel2','$2b$12$IfwGLoPZ7MyNhEV4TWS.ueS/SGtn0u5u0TdM5iPAxGTiGLuHwgswW',1,5,3,'c831252e58efa84454ea6b9e1dc32128','YGF','2025-08-27 10:32:26','2025-08-27 10:34:20'),(48,'Pavel3','$2b$12$Gmt4dj2mOza6gV9QL8hT..Vt6IT/y5HTCtRFVbdum8m8krvYAn27y',4,9,2,'162d419608d9698ae358aaa7f0e74df1',NULL,'2025-08-27 10:33:08','2025-08-27 10:33:17'),(49,'Pavel4','$2b$12$4IdQ4skDfnpWDjgmBTyfVu/TtDCKCH1mEng9pRvWh2zmV3Uz9HdUK',3,9,2,NULL,NULL,'2025-08-27 10:34:12',NULL);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_answers`
--

DROP TABLE IF EXISTS `user_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `attempt_id` int NOT NULL,
  `question_id` int NOT NULL,
  `answer` json NOT NULL,
  `is_correct` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `attempt_id` (`attempt_id`),
  KEY `question_id` (`question_id`),
  KEY `ix_user_answers_id` (`id`),
  CONSTRAINT `user_answers_ibfk_1` FOREIGN KEY (`attempt_id`) REFERENCES `user_quiz_attempts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_answers_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_answers`
--

LOCK TABLES `user_answers` WRITE;
/*!40000 ALTER TABLE `user_answers` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_answers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_quiz_attempts`
--

DROP TABLE IF EXISTS `user_quiz_attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_quiz_attempts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `quiz_id` int NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `score` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `quiz_id` (`quiz_id`),
  KEY `ix_user_quiz_attempts_id` (`id`),
  CONSTRAINT `user_quiz_attempts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_quiz_attempts_ibfk_2` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_quiz_attempts`
--

LOCK TABLES `user_quiz_attempts` WRITE;
/*!40000 ALTER TABLE `user_quiz_attempts` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_quiz_attempts` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-27 13:45:06

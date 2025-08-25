<template>
  <div class="image-display">
    <div v-if="images && images.length > 0" class="mt-3">
      <h6 class="text-muted mb-2">
        <i class="fas fa-images me-2"></i>
        Релевантные изображения ({{ images.length }})
        <small class="text-muted ms-2">
          Отсортированы по релевантности к тексту
        </small>
      </h6>
      
      <div class="image-grid">
        <div 
          v-for="(image, index) in images" 
          :key="index" 
          class="image-item"
          @click="openImageModal(image, index)"
        >
          <div class="image-container">
            <img 
              :src="image.data" 
              :alt="image.filename || `Изображение ${index + 1}`"
              class="image-thumbnail"
              loading="lazy"
            />
            <div class="image-overlay">
              <i class="fas fa-expand"></i>
            </div>
            
            <!-- Индикатор релевантности -->
            <div class="relevance-indicator" :class="getRelevanceClass(image.relevance_score)">
              {{ Math.round((image.relevance_score || 0) * 100) }}%
            </div>
          </div>
          
          <div class="image-info">
            <div class="image-title">
              <small class="text-muted">
                {{ getImageInfo(image) }}
              </small>
            </div>
            
            <!-- Контекст изображения -->
            <div v-if="image.context" class="image-context">
              <small class="text-muted">
                {{ getContextPreview(image.context) }}
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Модальное окно для просмотра изображения -->
    <div 
      class="modal fade" 
      id="imageModal" 
      tabindex="-1" 
      aria-labelledby="imageModalLabel" 
      aria-hidden="true"
    >
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="imageModalLabel">
              {{ selectedImage ? (selectedImage.filename || `Изображение ${selectedImageIndex + 1}`) : '' }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center">
            <img 
              v-if="selectedImage"
              :src="selectedImage.data" 
              :alt="selectedImage.filename || `Изображение ${selectedImageIndex + 1}`"
              class="img-fluid"
              style="max-height: 70vh;"
            />
            
            <!-- Информация о релевантности -->
            <div v-if="selectedImage && selectedImage.relevance_score !== undefined" class="mt-3">
              <div class="alert alert-info">
                <strong>Релевантность к тексту:</strong> {{ Math.round((selectedImage.relevance_score || 0) * 100) }}%
                <div class="progress mt-2" style="height: 8px;">
                  <div 
                    class="progress-bar" 
                    :class="getRelevanceClass(selectedImage.relevance_score)"
                    :style="{ width: (selectedImage.relevance_score || 0) * 100 + '%' }"
                  ></div>
                </div>
              </div>
            </div>
            
            <div v-if="selectedImage && selectedImage.context" class="mt-3">
              <h6>Контекст изображения:</h6>
              <p class="text-muted">{{ selectedImage.context }}</p>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button 
              v-if="selectedImage" 
              type="button" 
              class="btn btn-primary"
              @click="downloadImage"
            >
              <i class="fas fa-download me-2"></i>
              Скачать
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'

export default {
  name: 'ImageDisplay',
  props: {
    images: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedImage: null,
      selectedImageIndex: 0,
      imageModal: null
    }
  },
  mounted() {
    this.imageModal = new Modal(document.getElementById('imageModal'))
  },
  methods: {
    getImageInfo(image) {
      let info = []
      
      if (image.type === 'pdf_image') {
        info.push(`Страница ${image.page}`)
      } else if (image.type === 'docx_image') {
        info.push('DOCX документ')
      } else if (image.type === 'single_image') {
        info.push('Изображение')
      }
      
      if (image.filename) {
        info.push(image.filename)
      }
      
      return info.join(' • ')
    },
    
    getContextPreview(context) {
      if (!context) return ''
      return context.length > 80 ? context.substring(0, 80) + '...' : context
    },
    
    getRelevanceClass(relevanceScore) {
      if (!relevanceScore) return 'relevance-low'
      
      if (relevanceScore >= 0.7) return 'relevance-high'
      if (relevanceScore >= 0.4) return 'relevance-medium'
      return 'relevance-low'
    },
    
    openImageModal(image, index) {
      this.selectedImage = image
      this.selectedImageIndex = index
      this.imageModal.show()
    },
    
    downloadImage() {
      if (!this.selectedImage) return
      
      try {
        // Создаем ссылку для скачивания
        const link = document.createElement('a')
        link.href = this.selectedImage.data
        link.download = this.selectedImage.filename || `image_${this.selectedImageIndex + 1}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (error) {
        console.error('Ошибка при скачивании изображения:', error)
        this.$emit('show-notification', 'Ошибка при скачивании изображения', 'error')
      }
    }
  }
}
</script>

<style scoped>
.image-display {
  margin-top: 1rem;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
  margin-top: 0.5rem;
}

.image-item {
  cursor: pointer;
  transition: transform 0.2s ease;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
  background: white;
}

.image-item:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-container {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
}

.image-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: filter 0.2s ease;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-overlay i {
  color: white;
  font-size: 1.5rem;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-item:hover .image-thumbnail {
  filter: brightness(0.8);
}

/* Индикатор релевантности */
.relevance-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: bold;
  min-width: 30px;
  text-align: center;
}

.relevance-high {
  background: rgba(40, 167, 69, 0.9) !important;
}

.relevance-medium {
  background: rgba(255, 193, 7, 0.9) !important;
}

.relevance-low {
  background: rgba(108, 117, 125, 0.9) !important;
}

.image-info {
  padding: 0.75rem;
  background: #f8f9fa;
}

.image-title {
  margin-bottom: 0.5rem;
}

.image-context {
  font-size: 0.75rem;
  line-height: 1.3;
  color: #6c757d;
  border-top: 1px solid #e9ecef;
  padding-top: 0.5rem;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.5rem;
  }
  
  .image-info {
    padding: 0.5rem;
  }
  
  .relevance-indicator {
    font-size: 0.6rem;
    padding: 1px 4px;
    min-width: 25px;
  }
}

/* Прогресс-бар для модального окна */
.progress-bar.relevance-high {
  background-color: #28a745;
}

.progress-bar.relevance-medium {
  background-color: #ffc107;
}

.progress-bar.relevance-low {
  background-color: #6c757d;
}
</style>

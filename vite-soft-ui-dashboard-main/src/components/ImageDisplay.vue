<template>
  <div class="image-display">
    <div v-if="images && images.length > 0" class="mt-3">
      <h6 class="text-muted mb-2">
        <i class="fas fa-images me-2"></i>
        Изображения из документа ({{ images.length }})
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
          </div>
          
          <div class="image-info">
            <small class="text-muted">
              {{ getImageInfo(image) }}
            </small>
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
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 0.5rem;
}

.image-item {
  cursor: pointer;
  transition: transform 0.2s ease;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.image-item:hover {
  transform: scale(1.05);
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

.image-info {
  padding: 0.5rem;
  background: #f8f9fa;
  font-size: 0.75rem;
  line-height: 1.2;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 768px) {
  .image-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.5rem;
  }
  
  .image-info {
    padding: 0.25rem;
    font-size: 0.7rem;
  }
}
</style>

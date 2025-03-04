// Like functionality
document.querySelectorAll('.like-btn').forEach(button => {
    button.addEventListener('click', function() {
        const postId = this.getAttribute('data-post-id');
        
        fetch(`/like/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update all instances of this post's like button (in feed and modals)
                document.querySelectorAll(`.like-btn[data-post-id="${postId}"]`).forEach(btn => {
                    const icon = btn.querySelector('i');
                    const likeCountElement = btn.closest('.actions').querySelector('.like-count');
                    
                    if (data.action === 'liked') {
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-danger');
                    } else {
                        icon.classList.remove('fas', 'text-danger');
                        icon.classList.add('far');
                    }
                    
                    if (likeCountElement) {
                        likeCountElement.textContent = data.likes;
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

// Comment functionality
document.querySelectorAll('.comment-form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const postId = this.getAttribute('data-post-id');
        const commentInput = this.querySelector('input[name="comment"]');
        const commentText = commentInput.value.trim();
        
        if (!commentText) return;
        
        fetch(`/comment/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `comment=${encodeURIComponent(commentText)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Find the comments container
                const commentsSection = this.closest('.modal-content, .card-body').querySelector('.comments-section');
                const commentsContainer = commentsSection.querySelector('.comments-container') || 
                                         commentsSection;
                
                // Create new comment element
                const newComment = document.createElement('div');
                newComment.className = 'comment mb-2';
                newComment.innerHTML = `
                    <strong>${data.comment.username}</strong> ${data.comment.body}
                    <small class="text-muted d-block">${data.comment.timestamp}</small>
                `;
                
                // Add comment to container
                commentsContainer.appendChild(newComment);
                
                // Update comment count if it exists
                const commentCountElements = document.querySelectorAll(`.comment-count[data-post-id="${postId}"]`);
                commentCountElements.forEach(element => {
                    const currentCount = parseInt(element.textContent || '0');
                    element.textContent = currentCount + 1;
                });
                
                // Clear input
                commentInput.value = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

// Show/hide comments
document.querySelectorAll('.view-comments-link').forEach(link => {
    link.addEventListener('click', function() {
        const commentsContainer = this.nextElementSibling;
        const commentCount = this.getAttribute('data-count');
        
        if (commentsContainer.style.display === 'none') {
            commentsContainer.style.display = 'block';
            this.textContent = 'Hide comments';
        } else {
            commentsContainer.style.display = 'none';
            this.textContent = `View all ${commentCount} comments`;
        }
    });
});

// Focus comment input when comment icon is clicked
document.querySelectorAll('.comment-btn').forEach(button => {
    button.addEventListener('click', function() {
        const form = this.closest('.modal-content, .card-body').querySelector('.comment-form');
        const input = form.querySelector('input[name="comment"]');
        input.focus();
    });
});

// Auto-resize textarea
document.querySelectorAll('textarea').forEach(textarea => {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        lables = {
            'group': 'Группа',
            'text': 'Сообщение'
        }
        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста'
        }
        fields = ['group', 'text', 'image']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}

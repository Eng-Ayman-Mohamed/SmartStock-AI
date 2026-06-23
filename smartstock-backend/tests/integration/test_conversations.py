import uuid

from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai.models import ChatConversation, ChatMessage
from apps.authentication.models import CustomUser


class ConversationViewSetTests(APITestCase):
    """Integration tests for /api/ai/conversations/"""

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            email='user@test.com',
            username='user@test.com',
            password='StrongPass123!',
            role='viewer',
        )
        cls.other = CustomUser.objects.create_user(
            email='other@test.com',
            username='other@test.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _url(self, path=''):
        return f'/api/ai/conversations/{path}'

    def _auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    # --- List ---

    def test_list_unauthenticated_returns_401(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_user_conversations_only(self):
        ChatConversation.objects.create(user=self.user, title='Mine')
        ChatConversation.objects.create(user=self.other, title='Theirs')
        self._auth(self.user)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['title'], 'Mine')

    def test_list_empty(self):
        self._auth(self.user)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'], [])

    # --- Create ---

    def test_create_unauthenticated_returns_401(self):
        response = self.client.post(self._url(), {'title': 'New'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_with_title(self):
        self._auth(self.user)
        response = self.client.post(self._url(), {'title': 'My Chat'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'My Chat')

    def test_create_without_title_uses_default(self):
        self._auth(self.user)
        response = self.client.post(self._url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['title'], 'New Conversation')

    def test_create_title_too_long_returns_422(self):
        self._auth(self.user)
        response = self.client.post(self._url(), {'title': 'x' * 201}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    # --- Retrieve ---

    def test_retrieve_returns_conversation_with_messages(self):
        conv = ChatConversation.objects.create(user=self.user, title='My Chat')
        ChatMessage.objects.create(conversation=conv, role='user', content='hello')
        ChatMessage.objects.create(conversation=conv, role='assistant', content='hi there')
        self._auth(self.user)
        response = self.client.get(self._url(f'{conv.id}/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['messages']), 2)
        self.assertEqual(response.data['data']['messages'][0]['content'], 'hello')

    def test_retrieve_other_users_returns_404(self):
        conv = ChatConversation.objects.create(user=self.other, title='Secret')
        self._auth(self.user)
        response = self.client.get(self._url(f'{conv.id}/'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_nonexistent_returns_404(self):
        self._auth(self.user)
        response = self.client.get(self._url(f'{uuid.uuid4()}/'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Rename (PATCH) ---

    def test_rename_success(self):
        conv = ChatConversation.objects.create(user=self.user, title='Old')
        self._auth(self.user)
        response = self.client.patch(self._url(f'{conv.id}/'), {'title': 'Renamed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conv.refresh_from_db()
        self.assertEqual(conv.title, 'Renamed')

    def test_rename_missing_title_returns_422(self):
        conv = ChatConversation.objects.create(user=self.user, title='Old')
        self._auth(self.user)
        response = self.client.patch(self._url(f'{conv.id}/'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_rename_other_users_returns_404(self):
        conv = ChatConversation.objects.create(user=self.other, title='Theirs')
        self._auth(self.user)
        response = self.client.patch(self._url(f'{conv.id}/'), {'title': 'Mine now'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Destroy ---

    def test_destroy_success(self):
        conv = ChatConversation.objects.create(user=self.user, title='To delete')
        self._auth(self.user)
        response = self.client.delete(self._url(f'{conv.id}/'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatConversation.objects.filter(pk=conv.id).exists())

    def test_destroy_other_users_returns_404(self):
        conv = ChatConversation.objects.create(user=self.other, title='Theirs')
        self._auth(self.user)
        response = self.client.delete(self._url(f'{conv.id}/'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Messages sub-resource ---

    def test_messages_returns_list(self):
        conv = ChatConversation.objects.create(user=self.user, title='Chat')
        ChatMessage.objects.create(conversation=conv, role='user', content='q1')
        ChatMessage.objects.create(conversation=conv, role='assistant', content='a1')
        self._auth(self.user)
        response = self.client.get(self._url(f'{conv.id}/messages/'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_messages_other_users_returns_404(self):
        conv = ChatConversation.objects.create(user=self.other, title='Private')
        self._auth(self.user)
        response = self.client.get(self._url(f'{conv.id}/messages/'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

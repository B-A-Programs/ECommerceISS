from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ISSEcommerceApp.models import Item, OrderedItem
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

class UserTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser', email='test@example.com', password='password123'
        )

    def test_create_user(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('password123'))

    def test_login_user(self):
        client = Client()
        login = client.login(username='testuser', password='password123')
        self.assertTrue(login)

    def test_register_existing_user(self):
        with self.assertRaises(Exception):
            get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')

class ItemTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            title='Test Shirt', description='A stylish shirt', price=20.0, category='S'
        )
    
    def test_item_creation(self):
        self.assertEqual(self.item.title, 'Test Shirt')
        self.assertEqual(self.item.price, 20.0)

class OrderedItemTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.item = Item.objects.create(title='Test Shirt', description='A stylish shirt', price=20.0, category='S')
        self.ordered_item = OrderedItem.objects.create(user=self.user, item=self.item, size='M', quantity=2)
    
    def test_ordered_item_creation(self):
        self.assertEqual(self.ordered_item.quantity, 2)
        self.assertEqual(self.ordered_item.size, 'M')

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.item = Item.objects.create(title='Test Shirt', description='A stylish shirt', price=20.0, category='S')
    
    def test_index_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_product_view(self):
        response = self.client.get(f'/product/{self.item.title}')
        self.assertEqual(response.status_code, 200)
    
    def test_login_view(self):
        response = self.client.post('/login', {'email': 'test@example.com', 'password': 'password123'})
        self.assertEqual(response.status_code, 200)
    
    def test_add_item(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(f'/add_item/{self.item.id}', {'quantity': 1, 'size': 'M'})
        self.assertEqual(response.status_code, 200)
    
    def test_add_invalid_quantity(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(f'/add_item/{self.item.id}', {'quantity': 10, 'size': 'M'})
        self.assertContains(response, "Quantity invalid or size not slected!", status_code=200)
    
    def test_checkout_requires_login(self):
        response = self.client.get('/checkout')
        self.assertEqual(response.status_code, 302)
    
    def test_order_creation(self):
        self.client.login(username='testuser', password='password123')
        self.client.post(f'/add_item/{self.item.id}', {'quantity': 1, 'size': 'M'})
        response = self.client.post('/order', {
            'country': 'USA', 'county': 'TestCounty', 'zip': '12345', 'address': '123 Street', 'city': 'TestCity'
        })
        self.assertContains(response, "Your order has been successfully sent", status_code=200)

class FailureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser', email='test@example.com', password='password123'
        )
        self.item = Item.objects.create(title='Test Shirt', description='A stylish shirt', price=20.0, category='S')
    
    def test_invalid_login(self):
        response = self.client.post('/login', {'email': 'test@example.com', 'password': 'wrongpassword'})
        self.assertContains(response, "Invalid username and/or password.", status_code=200)

    def test_register_mismatched_passwords(self):
        response = self.client.post('/register', {
            'email': 'new@example.com',
            'first_name': 'First',
            'last_name': 'Last',
            'password': 'abc123',
            'confirmation': 'abc321'
        })
        self.assertContains(response, "Passwords must match.", status_code=200)

    def test_add_item_without_size(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(f'/add_item/{self.item.id}', {'quantity': 2})
        self.assertContains(response, "Quantity invalid or size not slected!", status_code=200)

    def test_order_page_empty_cart(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post('/order', {
            'country': 'USA', 'county': 'County', 'zip': '12345', 'address': '123 Street', 'city': 'City'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to checkout if cart is empty

    def test_invalid_page_index(self):
        response = self.client.get('/?page=9999')
        self.assertContains(response, "You have selected a nonexistent page.", status_code=200)

    def test_decrease_quantity_below_one(self):
        self.client.login(username='testuser', password='password123')
        ordered_item = OrderedItem.objects.create(user=self.user, item=self.item, size='M', quantity=1)
        response = self.client.post(f'/decrease/{ordered_item.id}')
        self.assertJSONEqual(str(response.content, encoding='utf8'),
                             {"error": "Quantity would become less than 1. Try delete button."})
        self.assertEqual(response.status_code, 401)

    def test_increase_quantity_above_nine(self):
        self.client.login(username='testuser', password='password123')
        ordered_item = OrderedItem.objects.create(user=self.user, item=self.item, size='M', quantity=9)
        response = self.client.post(f'/increase/{ordered_item.id}')
        self.assertJSONEqual(str(response.content, encoding='utf8'),
                             {"error": "You can't order more than 9 of one type of item."})
        self.assertEqual(response.status_code, 403)

    def test_delete_item_wrong_method(self):
        self.client.login(username='testuser', password='password123')
        ordered_item = OrderedItem.objects.create(user=self.user, item=self.item, size='M', quantity=1)
        response = self.client.get(f'/delete/{ordered_item.id}')
        self.assertJSONEqual(str(response.content, encoding='utf8'), {"error": "POST method required!"})
        self.assertEqual(response.status_code, 402)

    def test_activation_invalid_token(self):
        url = "http://127.0.0.1:8000/activate/(%3FPMTA%5B0-9A-Za-z_%5C-%5D+)/(%3FPcolz62-aadf9137e1a1da3af01e217133d02f28%5B0-9A-Za-z%5D%7B1,13%7D-%5B0-9A-Za-z%5D%7B1,20%7D)/"
        response = self.client.get(url)
        self.assertContains(response, "Activation link is invalid!", status_code=200)

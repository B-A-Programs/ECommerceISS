from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ISSEcommerceApp.models import Item, OrderedItem

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
// MongoDB holds two collections deliberately unsuited to a relational
// schema: the product catalog (variable attributes per category — a
// keyboard has "switch_type", a monitor has "refresh_hz") and past
// support chat sessions (a variable-length array of turns per document).
// This is the natural home for "semi-structured" data in the demo.

db = db.getSiblingDB('supportgraph');

db.createCollection('products');
db.products.insertMany([
  {
    sku: 'KEY-100', name: 'Mechanical Keyboard 100', category: 'peripherals',
    price: 79.0, stock: 42, tags: ['keyboard', 'mechanical', 'office'],
    attributes: { switch_type: 'brown', backlight: true, layout: 'ISO' },
  },
  {
    sku: 'MOU-200', name: 'Ergo Mouse 200', category: 'peripherals',
    price: 45.0, stock: 87, tags: ['mouse', 'ergonomic'],
    attributes: { dpi: 1600, wireless: true },
  },
  {
    sku: 'MON-270', name: 'Monitor 27" QHD', category: 'displays',
    price: 249.5, stock: 15, tags: ['monitor', 'qhd'],
    attributes: { size_inches: 27, resolution: '2560x1440', refresh_hz: 75 },
  },
  {
    sku: 'DSK-STND', name: 'Standing Desk', category: 'furniture',
    price: 340.0, stock: 8, tags: ['desk', 'standing', 'furniture'],
    attributes: { width_cm: 140, motorised: true },
  },
  {
    sku: 'HDS-300', name: 'Wireless Headset 300', category: 'audio',
    price: 89.0, stock: 30, tags: ['headset', 'wireless', 'audio'],
    attributes: { battery_hours: 20, noise_cancelling: true },
  },
  {
    sku: 'MIC-400', name: 'USB Microphone 400', category: 'audio',
    price: 76.5, stock: 22, tags: ['microphone', 'streaming', 'audio'],
    attributes: { polar_pattern: 'cardioid' },
  },
  {
    sku: 'SPK-500', name: 'Desktop Speakers 500', category: 'audio',
    price: 64.99, stock: 50, tags: ['speakers', 'audio'],
    attributes: { wattage: 20 },
  },
  {
    sku: 'CAB-050', name: 'USB-C Cable 1m', category: 'accessories',
    price: 14.75, stock: 300, tags: ['cable', 'accessory'],
    attributes: { length_m: 1 },
  },
  {
    sku: 'MAT-010', name: 'Desk Mat XL', category: 'accessories',
    price: 19.9, stock: 120, tags: ['mat', 'accessory'],
    attributes: { size: 'XL' },
  },
]);
db.products.createIndex({ sku: 1 }, { unique: true });
db.products.createIndex({ name: 'text', tags: 'text' });

db.createCollection('support_sessions');
db.support_sessions.insertMany([
  {
    session_id: 'S-1001',
    customer_id: 1,
    started_at: new Date('2025-05-18T09:12:00Z'),
    resolved: true,
    channel: 'chat',
    messages: [
      { role: 'customer', text: 'My headset arrived with a broken cable, can I return it?' },
      { role: 'agent', text: 'Yes, since it is within 30 days we can process a return with a prepaid label.' },
    ],
  },
  {
    session_id: 'S-1002',
    customer_id: 3,
    started_at: new Date('2025-02-27T14:03:00Z'),
    resolved: true,
    channel: 'email',
    messages: [
      { role: 'customer', text: 'The monitor has dead pixels, I want a refund not a replacement.' },
      { role: 'agent', text: 'Understood, refunds for defective units are approved without needing a replacement first.' },
    ],
  },
  {
    session_id: 'S-1003',
    customer_id: 5,
    started_at: new Date('2023-10-08T11:45:00Z'),
    resolved: false,
    channel: 'chat',
    messages: [
      { role: 'customer', text: 'Second time this headset has a battery issue, quite frustrating.' },
    ],
  },
]);
db.support_sessions.createIndex({ customer_id: 1 });
db.support_sessions.createIndex({ session_id: 1 }, { unique: true });

print('supportgraph: seeded products and support_sessions collections.');

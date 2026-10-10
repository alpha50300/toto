// تثبيت المكتبات: npm install express dotenv cors
require('dotenv').config();
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.static('.')); // تشغيل ملف index.html تلقائياً

// نقطة جلب بيانات الفيلم تلقائياً من TMDB دون إظهار API Key للعامة
app.get('/api/info/:type/:id', async (req, res) => {
    const { type, id } = req.params;
    const apiKey = process.env.TMDB_API_KEY;

    try {
        const response = await fetch(`https://api.themoviedb.org/3/${type}/${id}?api_key=${apiKey}&language=ar-SA`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'حدث خطأ أثناء جلب البيانات' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 السيرفر يعمل على: http://localhost:${PORT}`));
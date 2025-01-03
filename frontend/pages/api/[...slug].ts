import { NextApiRequest, NextApiResponse } from 'next';

const BACKEND_URL = process.env.BACKEND_URL || 'http://backend-chart:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { method } = req;
  const { slug } = req.query;

  const path = Array.isArray(slug) ? slug.join('/') : slug;

  console.log("Send to backend via url build with slug logic:  " + `${BACKEND_URL}/${path}`)

  try {
    const response = await fetch(`${BACKEND_URL}/${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: method !== 'GET' ? JSON.stringify(req.body) : undefined,
    });

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Error in proxy handler:', error);
    res.status(500).json({ message: 'Internal Server Error' });
  }
} 
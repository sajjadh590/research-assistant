// کلید API کاملاً حذف شده و مدیریت آن به بک‌اند واگذار شده است.
const API_PROXY_URL = "/api/chat/completions"; // آدرس نسبی به endpoint پراکسی در بک‌اند


async function callLlm(messages) {
    const response = await fetch(API_PROXY_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            // مدل و پیام‌ها توسط فرانت‌اند به بک‌اند ارسال می‌شوند
            model: "mistralai/mistral-7b-instruct:free",
            messages: messages
        })
    });


    if (!response.ok) {
        const error = await response.json();
        console.error("API Proxy Error:", error);
        throw new Error("Failed to get response from backend proxy. Check server logs for details.");
    }


    const data = await response.json();
    return data.choices[0].message.content;
}


export async function findArticles(query) {
    const prompt = `You are a research assistant API. A user is searching for academic articles on the topic: "${query}".
Your task is to find and return a list of 5 relevant, real academic articles.
For each article, provide the following details in a JSON object: id, title, authors (as a string), journal, year, a short abstract in Persian, citations (a realistic number), and a placeholder pdf_url ('#').
The final output MUST be a valid JSON array of these objects. Do not include any other text, explanation, or markdown formatting like \`\`\`json. Just the raw array.


Example for one article:
{
    "id": 1,
    "title": "Attention Is All You Need",
    "authors": "Ashish Vaswani, et al.",
    "journal": "NIPS",
    "year": 2017,
    "abstract": "این مقاله یک معماری شبکه جدید به نام ترنسفورمر را معرفی می‌کند که تنها بر اساس مکانیزم‌های توجه است و کاملاً از تکرار و کانولوشن صرف نظر می‌کند.",
    "citations": 85000,
    "pdf_url": "#"
}`;


    const responseContent = await callLlm([{ role: "user", content: prompt }]);
    
    try {
        // پاکسازی پاسخ برای اطمینان از اینکه فقط JSON خالص وجود دارد
        const cleanedResponse = responseContent.substring(responseContent.indexOf('['), responseContent.lastIndexOf(']') + 1);
        const articles = JSON.parse(cleanedResponse);
        return {
            results_count: articles.length,
            articles: articles
        };
    } catch (e) {
        console.error("Error parsing JSON from LLM response:", e, "Response was:", responseContent);
        throw new Error("Could not understand the data format from the AI. The response was not valid JSON.");
    }
}


export async function generateProposal(topic, sections) {
    const sectionsString = sections.map(s => `- Section "${s.title}": ${s.instructions || 'Generate standard academic content for this section.'}`).join('\n');
    const prompt = `You are a professional academic writer. Your task is to write a detailed research proposal in Persian.
The main topic is: "${topic}".
The proposal must strictly follow this structure and instructions:
${sectionsString}


Generate the content for each section. The output should be well-structured, academic, and sound like it was written by a human researcher. Use Markdown for formatting (e.g., # for main title, ## for section titles, lists, bold text). Start with the main title of the proposal.`;


    return await callLlm([{ role: "user", content: prompt }]);
}

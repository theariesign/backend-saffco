document.addEventListener("DOMContentLoaded", () => {
  const articlesSection = document.getElementById("articles-section");
  const productsSection = document.getElementById("products-section");
  const articlesTab = document.getElementById("articles-tab");
  const productsTab = document.getElementById("products-tab");

  // Toggle sections
  articlesTab.addEventListener("click", () => {
    articlesSection.classList.remove("hidden");
    productsSection.classList.add("hidden");
    loadArticles();
  });

  productsTab.addEventListener("click", () => {
    productsSection.classList.remove("hidden");
    articlesSection.classList.add("hidden");
    loadProducts();
  });

  // Fetch and display articles
  async function loadArticles() {
    const response = await fetch("/articles");
    const data = await response.json();
    const articlesList = document.getElementById("articles-list");
    articlesList.innerHTML = "";
    data.articles.forEach((article) => {
      const li = document.createElement("li");
      li.innerHTML = `
          <h3>${article.title}</h3>
          <p>${article.content}</p>
          <img src="${article.image_path}" alt="${article.title}" style="max-width:100px;">
          <button class="delete-btn" onclick="deleteArticle(${article.id})">Delete</button>
        `;
      articlesList.appendChild(li);
    });
  }

  // Add article
  const articleForm = document.getElementById("article-form");
  articleForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("article-title").value;
    const content = document.getElementById("article-content").value;
    const image = document.getElementById("article-image").value;

    const response = await fetch("/admin/articles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content, image_path: image }),
    });

    if (response.ok) {
      alert("Article added!");
      loadArticles();
    } else {
      alert("Failed to add article");
    }
  });

  // Delete article
  async function deleteArticle(id) {
    const response = await fetch(`/admin/articles/${id}`, { method: "DELETE" });
    if (response.ok) {
      alert("Article deleted!");
      loadArticles();
    } else {
      alert("Failed to delete article");
    }
  }

  // Fetch and display products
  async function loadProducts() {
    const response = await fetch("/products"); // Adjust this endpoint if needed
    const data = await response.json();
    const productsList = document.getElementById("products-list");
    productsList.innerHTML = "";
    data.products.forEach((product) => {
      const li = document.createElement("li");
      li.innerHTML = `
          <h3>${product.product_name}</h3>
          <p>${product.description}</p>
          <p>Price: ${product.price}</p>
          <img src="${product.product_image_url}" alt="${product.product_name}" style="max-width:100px;">
          <button class="delete-btn" onclick="deleteProduct(${product.id})">Delete</button>
        `;
      productsList.appendChild(li);
    });
  }

  // Add product
  const productForm = document.getElementById("product-form");
  productForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("product-name").value;
    const image = document.getElementById("product-image").value;
    const description = document.getElementById("product-description").value;
    const price = document.getElementById("product-price").value;

    const response = await fetch("/admin/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_name: name,
        product_image_url: image,
        description,
        price,
      }),
    });

    if (response.ok) {
      alert("Product added!");
      loadProducts();
    } else {
      alert("Failed to add product");
    }
  });

  // Delete product
  async function deleteProduct(id) {
    const response = await fetch(`/admin/products/${id}`, { method: "DELETE" });
    if (response.ok) {
      alert("Product deleted!");
      loadProducts();
    } else {
      alert("Failed to delete product");
    }
  }
});

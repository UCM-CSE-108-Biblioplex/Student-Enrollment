document.addEventListener("alpine:init", () => {
    Alpine.data("adminUsers", () => ({
      users: [],
      loading: true,
      searchQuery: "",
      searchTimeout: null,
      
      // Pagination state
      currentPage: 1,
      perPage: 10,
      totalUsers: 0,
      totalPages: 1,
      
      // Modal state
      showEditModal: false,
      showDeleteModal: false,
      editingUser: {},
      deletingUser: {},
      saving: false,
      deleting: false,
      
      init() {
        this.fetchUsers();
      },
      
      // Fetch users from the API
      async fetchUsers() {
        this.loading = true;
        try {
          const params = new URLSearchParams({
            page: this.currentPage,
            per_page: this.perPage
          });
          
          if (this.searchQuery) {
            params.append("username", this.searchQuery);
          }
          
          const response = await fetch(`/api/v1/users?${params}`);
          if (!response.ok) {
            throw new Error("Failed to fetch users");
          }
          
          const data = await response.json();
          this.users = data;
          
          // For pagination - in a real app, the API would return metadata
          // This is a simplified version assuming we get total count from headers or response
          this.totalUsers = data.length > 0 ? data.length * this.totalPages : 0;
          this.totalPages = Math.ceil(this.totalUsers / this.perPage);
        } catch (error) {
          console.error("Error fetching users:", error);
          this.users = [];
        } finally {
          this.loading = false;
        }
      },
      
      // Debounced search function
      debouncedSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
          this.currentPage = 1; // Reset to first page on new search
          this.fetchUsers();
        }, 500); // 500ms debounce
      },
      
      // Pagination methods
      get startIndex() {
        return (this.currentPage - 1) * this.perPage;
      },
      
      get endIndex() {
        return this.startIndex + this.perPage;
      },
      
      get displayedPages() {
        const pages = [];
        const maxVisiblePages = 5;
        
        if (this.totalPages <= maxVisiblePages) {
          // Show all pages if there are few
          for (let i = 1; i <= this.totalPages; i++) {
            pages.push(i);
          }
        } else {
          // Always show first page
          pages.push(1);
          
          // Calculate middle pages
          let startPage = Math.max(2, this.currentPage - 1);
          let endPage = Math.min(this.totalPages - 1, this.currentPage + 1);
          
          // Adjust if we're near the beginning
          if (this.currentPage <= 3) {
            endPage = 4;
          }
          
          // Adjust if we're near the end
          if (this.currentPage >= this.totalPages - 2) {
            startPage = this.totalPages - 3;
          }
          
          // Add ellipsis if needed before middle pages
          if (startPage > 2) {
            pages.push("...");
          }
          
          // Add middle pages
          for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
          }
          
          // Add ellipsis if needed after middle pages
          if (endPage < this.totalPages - 1) {
            pages.push("...");
          }
          
          // Always show last page
          pages.push(this.totalPages);
        }
        
        return pages;
      },
      
      prevPage() {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.fetchUsers();
        }
      },
      
      nextPage() {
        if (this.currentPage < this.totalPages) {
          this.currentPage++;
          this.fetchUsers();
        }
      },
      
      goToPage(page) {
        if (page !== this.currentPage) {
          this.currentPage = page;
          this.fetchUsers();
        }
      },
      
      // User formatting
      formatName(user) {
        let name = user.first_name;
        if (user.middle_name) {
          name += ` ${user.middle_name}`;
        }
        name += ` ${user.last_name}`;
        return name;
      },
      
      // Modal methods
      openCreateModal() {
        this.editingUser = {
          first_name: "",
          middle_name: "",
          last_name: "",
          username: "",
          email: "",
          password: "",
          is_admin: false
        };
        this.showEditModal = true;
      },
      
      openEditModal(user) {
        this.editingUser = { ...user, password: "" };
        this.showEditModal = true;
      },
      
      closeEditModal() {
        this.showEditModal = false;
        this.saving = false;
        // Clear after animation completes
        setTimeout(() => {
          this.editingUser = {};
        }, 300);
      },
      
      openDeleteModal(user) {
        this.deletingUser = { ...user };
        this.showDeleteModal = true;
      },
      
      closeDeleteModal() {
        this.showDeleteModal = false;
        this.deleting = false;
        // Clear after animation completes
        setTimeout(() => {
          this.deletingUser = {};
        }, 300);
      },
      
      // CRUD operations
      async saveUser() {
        this.saving = true;
        
        try {
          const isNewUser = !this.editingUser.id;
          const method = isNewUser ? "POST" : "PUT";
          const userData = { ...this.editingUser };
          
          // Don't send empty password for existing users
          if (!isNewUser && !userData.password) {
            delete userData.password;
          }
          
          const response = await fetch("/api/v1/users", {
            method,
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(userData)
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to save user");
          }
          
          // Refresh the user list
          await this.fetchUsers();
          this.closeEditModal();
        } catch (error) {
          console.error("Error saving user:", error);
          alert(`Error: ${error.message}`);
        } finally {
          this.saving = false;
        }
      },
      
      async deleteUser() {
        this.deleting = true;
        
        try {
          const response = await fetch("/api/v1/users", {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ user_id: this.deletingUser.id })
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to delete user");
          }
          
          // Refresh the user list
          await this.fetchUsers();
          this.closeDeleteModal();
        } catch (error) {
          console.error("Error deleting user:", error);
          alert(`Error: ${error.message}`);
        } finally {
          this.deleting = false;
        }
      }
    }));
  });
  
import { renderDashboard } from './views/dashboard.js';
import { renderNewProposal, attachNewProposalListeners } from './views/new_proposal.js';
import { renderSearchResults, attachSearchResultsListeners } from './views/search_results.js';
import { renderMetaAnalysis } from './views/meta_analysis.js';


document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('main-content');
    const navLinks = document.querySelectorAll('.nav-link[data-view]');


    const views = {
        'dashboard': { render: renderDashboard },
        'new-proposal': { render: renderNewProposal, afterRender: attachNewProposalListeners },
        'search': { render: renderSearchResults, afterRender: attachSearchResultsListeners },
        'meta-analysis': { render: renderMetaAnalysis },
    };


    const renderView = (viewName) => {
        const view = views[viewName];
        if (!view) {
            mainContent.innerHTML = `<div class="text-center"><h1 class="text-2xl font-bold">404 - صفحه یافت نشد</h1></div>`;
            return;
        }


        mainContent.innerHTML = view.render();
        if (view.afterRender) {
            view.afterRender();
        }


        lucide.createIcons();
        updateActiveLink(viewName);
    };


    const updateActiveLink = (activeView) => {
        navLinks.forEach(link => {
            if (link.dataset.view === activeView) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    };


    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewName = e.currentTarget.dataset.view;
            window.history.pushState({ view: viewName }, '', `#${viewName}`);
            renderView(viewName);
        });
    });


    const handlePopState = (e) => {
        const viewName = e.state ? e.state.view : (window.location.hash.substring(1) || 'dashboard');
        renderView(viewName);
    };


    window.addEventListener('popstate', handlePopState);


    const initialView = window.location.hash.substring(1) || 'dashboard';
    renderView(initialView);


    lucide.createIcons();
});

#!/usr/bin/env python3
"""Example usage of the PDF RAG pipeline."""

import os
from pathlib import Path
from src.rag_pipeline import RAGPipeline
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    """Demonstrate the PDF RAG pipeline functionality."""
    
    # Create sample data directory
    Path("./data/pdfs").mkdir(parents=True, exist_ok=True)
    
    console.print(Panel.fit(
        "[bold cyan]PDF RAG Pipeline Example[/bold cyan]\n"
        "Demonstrating document processing and search capabilities",
        border_style="cyan"
    ))
    
    # Check for environment setup
    if not os.getenv("NOMIC_API_KEY"):
        console.print("\n[yellow]Note: No NOMIC_API_KEY found. Using local embeddings.[/yellow]")
        use_local = True
    else:
        use_local = False
    
    # Initialize the pipeline
    console.print("\n[cyan]1. Initializing RAG Pipeline...[/cyan]")
    pipeline = RAGPipeline(use_local_embeddings=use_local)
    console.print("[green]✓[/green] Pipeline initialized")
    
    # Check for sample PDFs
    pdf_dir = Path("./data/pdfs")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        console.print("\n[yellow]No PDF files found in ./data/pdfs/[/yellow]")
        console.print("Please add some PDF files to ./data/pdfs/ and run this script again.")
        console.print("\nExample commands to use after adding PDFs:")
        console.print("  [cyan]python cli.py parse ./data/pdfs/[/cyan]")
        console.print("  [cyan]python cli.py search[/cyan]")
        console.print("  [cyan]python cli.py query[/cyan]")
        return
    
    # Process PDFs
    console.print(f"\n[cyan]2. Processing {len(pdf_files)} PDF files...[/cyan]")
    
    for pdf_file in pdf_files[:3]:  # Process first 3 PDFs as example
        console.print(f"   Processing: {pdf_file.name}")
        try:
            parsed_doc = pipeline.process_pdf(str(pdf_file))
            console.print(f"   [green]✓[/green] {parsed_doc.pages} pages, {len(parsed_doc.tables)} tables")
        except Exception as e:
            console.print(f"   [red]✗[/red] Error: {str(e)}")
    
    # Save the index
    console.print("\n[cyan]3. Saving index...[/cyan]")
    pipeline.save_index()
    console.print("[green]✓[/green] Index saved")
    
    # Show statistics
    stats = pipeline.get_statistics()
    console.print("\n[cyan]4. Index Statistics:[/cyan]")
    console.print(f"   • Total chunks: {stats['total_documents']}")
    console.print(f"   • Index size: {stats['index_size']}")
    console.print(f"   • Memory usage: {stats['memory_usage_mb']:.2f} MB")
    
    # Example searches
    if stats['total_documents'] > 0:
        console.print("\n[cyan]5. Example Searches:[/cyan]")
        
        example_queries = [
            "introduction",
            "methodology",
            "results",
            "conclusion"
        ]
        
        for query in example_queries:
            console.print(f"\n   [bold]Query:[/bold] '{query}'")
            results = pipeline.search(query, k=2)
            
            if results:
                for i, result in enumerate(results, 1):
                    content_preview = result['content'][:100] + "..."
                    console.print(f"   [{i}] Score: {result['score']:.4f}")
                    console.print(f"       {content_preview}")
            else:
                console.print("   No results found")
    
    # Demonstrate query functionality
    console.print("\n[cyan]6. Example Question Answering:[/cyan]")
    
    if stats['total_documents'] > 0:
        question = "What are the main topics discussed?"
        console.print(f"   [bold]Question:[/bold] {question}")
        
        response = pipeline.query(question, k=3)
        console.print(f"   [bold]Retrieved {response['num_results']} relevant passages[/bold]")
        
        if 'sources' in response:
            for i, source in enumerate(response['sources'][:2], 1):
                console.print(f"\n   Source {i}: {Path(source['source']).name}")
                console.print(f"   Score: {source['score']:.4f}")
                console.print(f"   Preview: {source['content']}")
    
    console.print("\n[green]✓[/green] Example completed successfully!")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Add more PDFs to ./data/pdfs/")
    console.print("2. Use the CLI for interactive search: [cyan]python cli.py search[/cyan]")
    console.print("3. Ask questions: [cyan]python cli.py query[/cyan]")
    console.print("4. View statistics: [cyan]python cli.py stats[/cyan]")


if __name__ == "__main__":
    main()
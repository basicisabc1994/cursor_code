#!/usr/bin/env python3
"""CLI interface for PDF RAG pipeline."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from src.rag_pipeline import RAGPipeline
from src.config import settings

# Setup rich console
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """PDF Document Processing and RAG Pipeline CLI."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold cyan]PDF RAG Pipeline[/bold cyan]\n"
        "Parse PDFs with Docling and search with FAISS + Nomic embeddings",
        border_style="cyan"
    ))


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--save-markdown', is_flag=True, default=True, help='Save markdown output')
@click.option('--output-dir', type=click.Path(), default='./data/processed', help='Output directory for markdown')
@click.option('--use-local', is_flag=True, help='Use local embeddings instead of Nomic')
def parse(pdf_path, save_markdown, output_dir, use_local):
    """Parse a PDF file or directory of PDFs."""
    pdf_path = Path(pdf_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Initialize pipeline
        task = progress.add_task("[cyan]Initializing pipeline...", total=None)
        
        try:
            pipeline = RAGPipeline(use_local_embeddings=use_local)
            progress.update(task, completed=True)
            
            if pdf_path.is_file():
                # Process single PDF
                task = progress.add_task(f"[cyan]Processing {pdf_path.name}...", total=None)
                parsed_doc = pipeline.process_pdf(str(pdf_path), save_markdown=save_markdown, output_dir=str(output_dir))
                progress.update(task, completed=True)
                
                # Display results
                console.print(f"\n[green]✓[/green] Successfully processed: [bold]{pdf_path.name}[/bold]")
                
                # Show document info
                table = Table(title="Document Information", show_header=False)
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Title", parsed_doc.title or "N/A")
                table.add_row("Pages", str(parsed_doc.pages))
                table.add_row("Tables", str(len(parsed_doc.tables)))
                table.add_row("Images", str(len(parsed_doc.images)))
                table.add_row("File Size", f"{pdf_path.stat().st_size / 1024:.2f} KB")
                
                console.print(table)
                
            elif pdf_path.is_dir():
                # Process directory
                task = progress.add_task(f"[cyan]Processing PDFs in {pdf_path}...", total=None)
                parsed_docs = pipeline.process_directory(str(pdf_path), save_markdown=save_markdown, output_dir=str(output_dir))
                progress.update(task, completed=True)
                
                # Display results
                console.print(f"\n[green]✓[/green] Successfully processed {len(parsed_docs)} PDFs")
                
                # Show summary table
                table = Table(title="Processed Documents")
                table.add_column("File", style="cyan")
                table.add_column("Pages", style="white")
                table.add_column("Tables", style="white")
                table.add_column("Chunks", style="white")
                
                for doc in parsed_docs:
                    table.add_row(
                        Path(doc.file_path).name,
                        str(doc.pages),
                        str(len(doc.tables)),
                        "✓"
                    )
                
                console.print(table)
            
            # Save index
            task = progress.add_task("[cyan]Saving index...", total=None)
            pipeline.save_index()
            progress.update(task, completed=True)
            
            # Show statistics
            stats = pipeline.get_statistics()
            console.print(f"\n[bold]Index Statistics:[/bold]")
            console.print(f"  • Total chunks: {stats['total_documents']}")
            console.print(f"  • Index size: {stats['index_size']}")
            console.print(f"  • Memory usage: {stats['memory_usage_mb']:.2f} MB")
            
        except Exception as e:
            console.print(f"[red]✗ Error: {str(e)}[/red]")
            sys.exit(1)


@cli.command()
@click.option('--k', default=5, help='Number of results to return')
@click.option('--use-local', is_flag=True, help='Use local embeddings instead of Nomic')
@click.option('--llm-provider', type=str, default=None, help="LLM provider (e.g., 'ollama')")
@click.option('--llm-model', type=str, default=None, help="LLM model name (e.g., 'llama3.2')")
def search(k, use_local, llm_provider, llm_model):
    """Interactive search interface."""
    try:
        # Initialize pipeline
        console.print("[cyan]Loading index...[/cyan]")
        pipeline = RAGPipeline(use_local_embeddings=use_local, llm_provider=llm_provider, llm_model=llm_model)
        
        # Check if index exists
        stats = pipeline.get_statistics()
        if stats['total_documents'] == 0:
            console.print("[yellow]⚠ No documents in index. Please parse some PDFs first.[/yellow]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Loaded index with {stats['total_documents']} chunks")
        console.print("\nEnter your search queries (type 'exit' to quit):\n")
        
        while True:
            # Get query from user
            query = Prompt.ask("[bold cyan]Query[/bold cyan]")
            
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            # Search
            with console.status("[cyan]Searching...[/cyan]"):
                results = pipeline.search(query, k=k)
            
            if not results:
                console.print("[yellow]No results found.[/yellow]\n")
                continue
            
            # Display results
            console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
            
            for i, result in enumerate(results, 1):
                # Create result panel
                content = result['content']
                if len(content) > 300:
                    content = content[:300] + "..."
                
                metadata = result['metadata']
                source = Path(metadata.get('source', 'Unknown')).name
                
                panel = Panel(
                    content,
                    title=f"[cyan]Result {i}[/cyan] | Score: {result['score']:.4f} | Source: {source}",
                    border_style="cyan" if i == 1 else "white"
                )
                console.print(panel)
            
            console.print()
        
        console.print("\n[cyan]Goodbye![/cyan]")
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--k', default=5, help='Number of documents to retrieve')
@click.option('--use-local', is_flag=True, help='Use local embeddings instead of Nomic')
@click.option('--llm-provider', type=str, default=None, help="LLM provider (e.g., 'ollama')")
@click.option('--llm-model', type=str, default=None, help="LLM model name (e.g., 'llama3.2')")
def query(k, use_local, llm_provider, llm_model):
    """Query the RAG system with questions."""
    try:
        # Initialize pipeline
        console.print("[cyan]Loading index...[/cyan]")
        pipeline = RAGPipeline(use_local_embeddings=use_local, llm_provider=llm_provider, llm_model=llm_model)
        
        # Check if index exists
        stats = pipeline.get_statistics()
        if stats['total_documents'] == 0:
            console.print("[yellow]⚠ No documents in index. Please parse some PDFs first.[/yellow]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Loaded index with {stats['total_documents']} chunks")
        console.print("\nAsk questions about your documents (type 'exit' to quit):\n")
        
        while True:
            # Get question from user
            question = Prompt.ask("[bold cyan]Question[/bold cyan]")
            
            if question.lower() in ['exit', 'quit', 'q']:
                break
            
            # Query
            with console.status("[cyan]Retrieving relevant documents...[/cyan]"):
                response = pipeline.query(question, k=k)
            
            # Display response
            console.print(f"\n[bold]Question:[/bold] {response['question']}")
            console.print(f"[bold]Retrieved {response['num_results']} relevant passages[/bold]\n")
            console.print(f"[bold]Answer:[/bold] {response.get('answer', '')}\n")
            
            # Show sources
            if 'sources' in response:
                for i, source in enumerate(response['sources'], 1):
                    console.print(f"[cyan]Source {i}:[/cyan] {Path(source['source']).name} (Score: {source['score']:.4f})")
                    console.print(f"  {source['content']}\n")
            
            # Show full context if requested
            if Confirm.ask("Show full retrieved context?", default=False):
                console.print("\n[bold]Full Context:[/bold]")
                console.print(Panel(response['context'], border_style="cyan"))
            
            console.print()
        
        console.print("\n[cyan]Goodbye![/cyan]")
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def stats():
    """Show statistics about the current index."""
    try:
        # Initialize pipeline
        pipeline = RAGPipeline()
        stats = pipeline.get_statistics()
        
        # Create statistics table
        table = Table(title="Index Statistics", show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Documents", str(stats['total_documents']))
        table.add_row("Index Size", str(stats['index_size']))
        table.add_row("Embedding Dimension", str(stats['dimension']))
        table.add_row("Memory Usage", f"{stats['memory_usage_mb']:.2f} MB")
        table.add_row("Processed PDFs", str(stats['processed_documents']))
        table.add_row("Total Pages", str(stats.get('total_pages', 0)))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
def clear():
    """Clear the current index."""
    if Confirm.ask("Are you sure you want to clear the index?", default=False):
        try:
            pipeline = RAGPipeline()
            pipeline.clear_index()
            console.print("[green]✓[/green] Index cleared successfully")
        except Exception as e:
            console.print(f"[red]✗ Error: {str(e)}[/red]")
            sys.exit(1)
    else:
        console.print("[yellow]Cancelled[/yellow]")


@cli.command()
@click.argument('index_path', type=click.Path())
def export(index_path):
    """Export the index to a file."""
    try:
        pipeline = RAGPipeline()
        pipeline.save_index(Path(index_path))
        console.print(f"[green]✓[/green] Index exported to {index_path}")
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('index_path', type=click.Path(exists=True))
def load(index_path):
    """Load an index from a file."""
    try:
        pipeline = RAGPipeline()
        pipeline.load_index(Path(index_path))
        stats = pipeline.get_statistics()
        console.print(f"[green]✓[/green] Loaded index with {stats['total_documents']} documents")
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()
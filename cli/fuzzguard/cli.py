import click


@click.group()
def cli():
    """FuzzGuard CLI - Automated LLM Red Teaming"""


@cli.command()
@click.option("--project", "-p", help="Project ID")
@click.option("--strategy", "-s", default="random", help="Selection strategy")
@click.option("--budget", "-b", default=1000, help="Query budget")
def run(project, strategy, budget):
    """Run a fuzzing job"""
    click.echo(f"Run: project={project}, strategy={strategy}, budget={budget}")


@cli.command()
@click.option("--job", "-j", help="Job ID")
def report(job):
    """Generate a report for a job"""
    click.echo(f"Report: job={job}")


@cli.command()
@click.argument("job_a")
@click.argument("job_b")
def diff(job_a, job_b):
    """Compare two job results"""
    click.echo(f"Diff: {job_a} vs {job_b}")


@cli.command()
@click.option("--model", "-m", help="Model to benchmark")
def benchmark(model):
    """Run a benchmark"""
    click.echo(f"Benchmark: model={model}")


if __name__ == "__main__":
    cli()

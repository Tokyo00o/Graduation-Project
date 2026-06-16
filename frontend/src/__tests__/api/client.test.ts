import { projectsApi, jobsApi, keysApi, providersApi, reportsApi, judgesApi, benchmarksApi } from '../../api/client';

describe('API client exports', () => {
  it('projectsApi has list, get, create, delete', () => {
    expect(projectsApi.list).toBeDefined();
    expect(projectsApi.get).toBeDefined();
    expect(projectsApi.create).toBeDefined();
    expect(projectsApi.delete).toBeDefined();
  });

  it('jobsApi.create accepts target_model', () => {
    const fn = jobsApi.create;
    expect(fn.length).toBe(2);
  });

  it('keysApi has list, set, delete, test', () => {
    expect(keysApi.list).toBeDefined();
    expect(keysApi.set).toBeDefined();
    expect(keysApi.delete).toBeDefined();
    expect(keysApi.test).toBeDefined();
  });

  it('providersApi has list', () => {
    expect(providersApi.list).toBeDefined();
  });

  it('reportsApi has get, summary, export functions', () => {
    expect(reportsApi.get).toBeDefined();
    expect(reportsApi.summary).toBeDefined();
    expect(reportsApi.exportJson).toBeDefined();
    expect(reportsApi.exportCsv).toBeDefined();
    expect(reportsApi.exportHtml).toBeDefined();
  });

  it('judgesApi has list and metrics', () => {
    expect(judgesApi.list).toBeDefined();
    expect(judgesApi.metrics).toBeDefined();
  });

  it('benchmarksApi has list', () => {
    expect(benchmarksApi.list).toBeDefined();
  });
});
